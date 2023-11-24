// --------------------------------------------------------------------
//      The MIT License (MIT)
//      
//      Copyright (c) 2021-2022 HRA! (t.hara)
//      
//      Permission is hereby granted, free of charge, to any person obtaining a copy
//      of this software and associated documentation files (the "Software"), to deal
//      in the Software without restriction, including without limitation the rights
//      to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//      copies of the Software, and to permit persons to whom the Software is
//      furnished to do so, subject to the following conditions:
//      
//      The above copyright notice and this permission notice shall be included in
//      all copies or substantial portions of the Software.
//      
//      THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//      IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//      FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//      AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//      LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//      OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
//      THE SOFTWARE.
// --------------------------------------------------------------------
//      2021/Jul/25th   t.hara  1st release
//      2022/Dec/03rd   t.hara  Modified for TinyUSB 0.14.0
//      2023/Nov/6th  uniskie Modified for pico sdk 1.5.1
//                            Modified joypad processing to use report descriptor

#include <stdio.h>
#include <string.h>
#include <pico/stdlib.h>
#include <pico/multicore.h>
#include <pico/time.h>
#if 0
#include <bsp/board_api.h> // 最新レポジトリの場合 2023/11/10
#else
#include <bsp/board.h>
#endif
#include <tusb.h>
#include <hardware/uart.h>

// --------------------------------------------------------------------
//      バージョン
// --------------------------------------------------------------------
#define USB_FAMEPAD_BRIDGE_FOR_MSX_VERSION "mod 2.5b / 24 Nov. 2023"

// --------------------------------------------------------------------
//      デバッグ：UUART(SERIAL)デバッグ文字列出力
// --------------------------------------------------------------------
#define DEBUG_UART_ON 1

// --------------------------------------------------------------------
//      デバッグ：USBレポート解析
//  0:なし / 1:接続時情報 / 2:接続&データ取得情報 / 3:データ解析
// --------------------------------------------------------------------
#define DEBUG_USE_ANALYSIS  1

// --------------------------------------------------------------------
//      TinyUSBの問題回避：
// * PS4コントローラーのマウントに失敗する問題の対策 *
// --------------------------------------------------------------------
// tusb_config.hで宣言しておく
static_assert( CFG_TUH_ENUMERATION_BUFSIZE > 499 );

// --------------------------------------------------------------------
//      TinyUSBの問題回避：
// * マウントが不安定なデバイス向けの対策 *
// * 8BITDO M30 は TinyUSB側の問題があるのでマウントには成功してもreport受信できない *
// * 恐らく XINPUTデバイス全般に非対応 *
// --------------------------------------------------------------------
// Pico SDK v1.5.1\pico-sdk\lib\tinyusb\src\portable\raspberrypi\rp2040\hcd_rp2040.c
// 591行付近
// hcd_setup_send内で _hw_endpoint_init を呼び出す手前あたりに sleep_ms(1); を追加する
// 例)
//  // EPX should be inactive
//  assert(!ep->active);
//  sleep_ms(1); //**customize** for 8BITDO M30
//
//  // EP0 out
//  _hw_endpoint_init(ep, dev_addr, 0x00, ep->wMaxPacketSize, 0, 0);
//  assert(ep->configured);


// --------------------------------------------------------------------
//      MSX の 上、下、左、右、A、B のボタンに対応する GPIOピンの開始番号
//
//      Start number of the GPIO pin corresponding to the Up, Down, Left, 
//      Right, A, and B buttons on the MSX.
//
#define MSX_BUTTON_PIN 2

// --------------------------------------------------------------------
//      MSX から来る SEL信号の GPIOピン番号
//
//      GPIO pin number of the SEL signal coming from the MSX
//
#define MSX_SEL_PIN 8

// --------------------------------------------------------------------
//      SEL信号の論理
//              0: 負論理 (MSX Joymega)
//              1: 正論理 (MegaDrive)
//
//      Logic of SEL signal
//              0: negative logic (MSX Joymega)
//              1: positive logic (MegaDrive)
#define MSX_SEL_LOGIC 0

// --------------------------------------------------------------------
//      SEL信号の論理反転ジャンパ
#define MD_SEL_PIN_O  14  // +3.3V -> 
#define MD_SEL_PIN_I  15  // <- +3.3V

// --------------------------------------------------------------------
// HID Device ID
uint16_t device_vid = -1;
uint16_t device_pid = -1;

// --------------------------------------------------------------------
// ゲームパッド認識状況
volatile uint8_t gamepad_poc_step = 0;

// --------------------------------------------------------------------
// レポート：アイテム用途ID
enum JOYPAD_ITEM_ID {
  joyitem_axis_x = 0,
  joyitem_axis_y,
  joyitem_axis_z,
  joyitem_axis_Rx,
  joyitem_axis_Ry,
  joyitem_axis_Rz,
  joyitem_hat_sw,               // 方向キー 0~7,null
  joyitem_button_1,
  joyitem_button_2,
  joyitem_button_3,
  joyitem_button_4,
  joyitem_button_5,
  joyitem_button_6,
  joyitem_button_7,
  joyitem_button_8,
  joyitem_button_9,
  joyitem_button_10,
  joyitem_button_11,
  joyitem_button_12,
  joyitem_button_13,
  joyitem_button_14,
  joyitem_button_15,
  joyitem_button_16,

  joyitem_count,

  joyitem_ng,

  joyitem_button_count = joyitem_count - joyitem_button_1,
};

// --------------------------------------------------------------------
//      X,Y軸感度
//
//      X,Y axis sensitivity
//
#define LEFT_THRESHOLD          -64
#define RIGHT_THRESHOLD         64
#define TOP_THRESHOLD           -64
#define BOTTOM_THRESHOLD        64

#define LEFT_THRESHOLD_JOYSTICK         (LEFT_THRESHOLD + 128)
#define RIGHT_THRESHOLD_JOYSTICK        (RIGHT_THRESHOLD + 128)
#define TOP_THRESHOLD_JOYSTICK          (TOP_THRESHOLD + 128)
#define BOTTOM_THRESHOLD_JOYSTICK       (BOTTOM_THRESHOLD + 128)

// --------------------------------------------------------------------
//      BUTTON MAP for Megadrive 6B Type
#define MD_A_BUTTON     (joyitem_button_3)   // [MD mini] A
#define MD_B_BUTTON     (joyitem_button_2)   // [MD mini] B
#define MD_C_BUTTON     (joyitem_button_6)   // [MD mini] C
#define MD_X_BUTTON     (joyitem_button_4)   // [MD mini] X
#define MD_Y_BUTTON     (joyitem_button_1)   // [MD mini] Y
#define MD_Z_BUTTON     (joyitem_button_5)   // [MD mini] Z
#define MD_START_BUTTON (joyitem_button_10)  // [MD mini] START
#define MD_MODE_BUTTON  (joyitem_button_9)   // [MD mini] MODE
// --------------------------------------------------------------------
//      BUTTON MAP for SFC/Nintendo SWITCH Type 
#define SFC_A_BUTTON     (joyitem_button_2)     // [SFC] B
#define SFC_B_BUTTON     (joyitem_button_1)     // [SFC] A
#define SFC_C_BUTTON     (joyitem_button_5)     // [SFC] L
#define SFC_X_BUTTON     (joyitem_button_4)     // [SFC] Y
#define SFC_Y_BUTTON     (joyitem_button_3)     // [SFC] X
#define SFC_Z_BUTTON     (joyitem_button_6)     // [SFC] R
#define SFC_START_BUTTON (joyitem_button_8)     // [SFC] START
#define SFC_MODE_BUTTON  (joyitem_button_7)     // [SFC] SELECT
// --------------------------------------------------------------------
//      BUTTON MAP for PS4 Type
#define PS4_A_BUTTON     (joyitem_button_2)   // [PS4] CROSS
#define PS4_B_BUTTON     (joyitem_button_3)   // [PS4] CIRCLE
#define PS4_C_BUTTON     (joyitem_button_5)   // [PS4] L1
#define PS4_X_BUTTON     (joyitem_button_1)   // [PS4] SQUARE
#define PS4_Y_BUTTON     (joyitem_button_4)   // [PS4] TRIANBLE
#define PS4_Z_BUTTON     (joyitem_button_6)   // [PS4] R1
#define PS4_START_BUTTON (joyitem_button_10)  // [PS4] START
#define PS4_MODE_BUTTON  (joyitem_button_9)   // [PS4] SELECT
// --------------------------------------------------------------------
//      BUTTON MAP for PS4 Fighting Commander Type
#define PS4FC_A_BUTTON     (joyitem_button_2)   // [PS4] CROSS
#define PS4FC_B_BUTTON     (joyitem_button_3)   // [PS4] CIRCLE
#define PS4FC_C_BUTTON     (joyitem_button_6)   // [PS4] R1
#define PS4FC_X_BUTTON     (joyitem_button_1)   // [PS4] SQUARE
#define PS4FC_Y_BUTTON     (joyitem_button_4)   // [PS4] TRIANBLE
#define PS4FC_Z_BUTTON     (joyitem_button_8)   // [PS4] R2 ※ PS4ではアナログ値だがボタンとしてもデータを返すので使える
#define PS4FC_START_BUTTON (joyitem_button_10)  // [PS4] START
#define PS4FC_MODE_BUTTON  (joyitem_button_9)   // [PS4] SELECT
// --------------------------------------------------------------------
//      BUTTON MAP for XBOX360 Type
#define XBOX_A_BUTTON     (joyitem_button_1)   // [XINPUT] A
#define XBOX_B_BUTTON     (joyitem_button_2)   // [XINPUT] B
#define XBOX_C_BUTTON     (joyitem_button_5)   // [XINPUT] LB
#define XBOX_X_BUTTON     (joyitem_button_3)   // [XINPUT] X
#define XBOX_Y_BUTTON     (joyitem_button_4)   // [XINPUT] Y
#define XBOX_Z_BUTTON     (joyitem_button_6)   // [XINPUT] RB
#define XBOX_START_BUTTON (joyitem_button_8)   // [XINPUT] START
#define XBOX_MODE_BUTTON  (joyitem_button_7)   // [XINPUT] BACK
// --------------------------------------------------------------------
//      BUTTON MAP for XBOX360 FIGHTING COMMANDER Type
#define XBOXFC_A_BUTTON     (joyitem_button_1)   // [XINPUT] A
#define XBOXFC_B_BUTTON     (joyitem_button_2)   // [XINPUT] B
#define XBOXFC_C_BUTTON     (joyitem_button_6)   // [XINPUT] RB
#define XBOXFC_X_BUTTON     (joyitem_button_3)   // [XINPUT] X
#define XBOXFC_Y_BUTTON     (joyitem_button_4)   // [XINPUT] Y
#define XBOXFC_Z_BUTTON     (joyitem_axis_Rz)    // [XINPUT] RT ※ 未検証かつXINPUTなので定義そのものが異なる
#define XBOXFC_START_BUTTON (joyitem_button_8)   // [XINPUT] START
#define XBOXFC_MODE_BUTTON  (joyitem_button_7)   // [XINPUT] BACK

// --------------------------------------------------------------------
//  BUTTON MAP (VARIABLE)
//  一旦、初期値はSFCタイプにする
static uint8_t volatile A_BUTTON     = SFC_A_BUTTON;
static uint8_t volatile B_BUTTON     = SFC_B_BUTTON;
static uint8_t volatile C_BUTTON     = SFC_C_BUTTON;
static uint8_t volatile X_BUTTON     = SFC_X_BUTTON;
static uint8_t volatile Y_BUTTON     = SFC_Y_BUTTON;
static uint8_t volatile Z_BUTTON     = SFC_Z_BUTTON;
static uint8_t volatile START_BUTTON = SFC_START_BUTTON;
static uint8_t volatile MODE_BUTTON  = SFC_MODE_BUTTON;

// --------------------------------------------------------------------
//      BUTTON MAP (VARIABLE)
// 
enum PAD_TYPE {
  PAD_TYPE_UNKNOWN = 0,
  PAD_TYPE_MD,      // MegaDrive Fighting6B (8 buttons )
  PAD_TYPE_SFC,     // SFC (8 buttons) / SWITCH (12 buttons)
  PAD_TYPE_PS4,     // PS4 (14 buttons) / PS3 (13 buttons)
  PAD_TYPE_PS4FG,   // FIGHTING COMMANDER PS4 (14 buttons) / PS3 (13 buttons)
  PAD_TYPE_XBOX,    // XBOX 360 Controller (XINPUT 13 buttons)
  PAD_TYPE_XBOXFG,  // FIGHTING COMMANDER XBOX 360 Controller (XINPUT 13 buttons)
};

static bool volatile need_detect_button_config = true;

#define ENABLE_PAD_NAME   1

#if ENABLE_PAD_NAME
  #define PAD_NAME(c) (c)
#else
  #define PAD_NAME(...)
#endif

// VID/PIDから設定を判定するリスト
typedef struct PAD_CONFIG_DEF {
  uint16_t vid;
  uint16_t pid;
  enum PAD_TYPE pad_type;
#if ENABLE_PAD_NAME
  char *pad_name;
#endif
} pad_foncig_def_t;
const pad_foncig_def_t pad_config_list[] = {
  // VID     HID     PAD_TYPE
  { 0x0CA3, 0x0024, PAD_TYPE_MD,      PAD_NAME("SEGA MegaDrive Mini Controller (10 buttons)") },
  { 0x054C, 0x05C4, PAD_TYPE_PS4,     PAD_NAME("Sony DUALSHOCK4 (14 buttons)") },
  { 0x054C, 0x09CC, PAD_TYPE_PS4,     PAD_NAME("Sony DUALSHOCK4 (14 buttons)") },
  { 0x0F0D, 0x00EE, PAD_TYPE_PS4,     PAD_NAME("Hori HORIPAD mini4 (14 buttons)") },
  { 0x1345, 0x1030, PAD_TYPE_SFC,     PAD_NAME("RETROFREAK Controller (10 buttons)") },
  { 0x0F0D, 0x0085, PAD_TYPE_PS4FG,   PAD_NAME("HORI FIGHTING COMMANDER PS4 [PS3 Mode] (13 buttons)") },
  { 0x0F0D, 0x0084, PAD_TYPE_PS4FG,   PAD_NAME("HORI FIGHTING COMMANDER PS4 [PS4 Mode] (14 buttons)") },
  { 0x0F0D, 0x008B, PAD_TYPE_PS4FG,   PAD_NAME("HORI RAP V HAYABUSA SILENT [PS3 Mode] (13 buttons)") },
  { 0x0F0D, 0x008A, PAD_TYPE_PS4FG,   PAD_NAME("HORI RAP V HAYABUSA SILENT [PS4 Mode] (14 buttons)") },

  // [未対応] XINPUTデバイス
  { 0x045E, 0x028E, PAD_TYPE_XBOX,    PAD_NAME("Microsoft XBOX 360 Controller (10 buttons)") },
  { 0x0F0D, 0x0086, PAD_TYPE_XBOXFG,  PAD_NAME("HORI FIGHTING COMMANDER PS4 [PC Mode] (10 buttons)") },
  { 0x0F0D, 0x008C, PAD_TYPE_XBOXFG,  PAD_NAME("HORI RAP V HAYABUSA SILENT [PC Mode] (10 buttons)") },
  { 0x045E, 0x028E, PAD_TYPE_XBOXFG,  PAD_NAME("8BITDO M30 2.4g (10 buttons)") },
  { 0x045E, 0x028E, PAD_TYPE_SFC,     PAD_NAME("CYBER Gadget GYRO CONTROLLER LITE CY-NSGYCL (12 buttons)") },

  // リスト終端
  { 0xFFFF, 0xFFFF, PAD_TYPE_UNKNOWN, PAD_NAME("Unknown") }, // end
};
enum { pad_config_list_count = sizeof(pad_config_list) / sizeof(pad_config_list[0]) };

// ボタン配置の切替
static void change_button_config( enum PAD_TYPE pad_type)
{
  switch (pad_type) {
  case PAD_TYPE_MD:
    #if DEBUG_UART_ON
      printf("PAD_TYPE:MegaDrive\r\n");
    #endif
    A_BUTTON     = MD_A_BUTTON;
    B_BUTTON     = MD_B_BUTTON;
    C_BUTTON     = MD_C_BUTTON;
    X_BUTTON     = MD_X_BUTTON;
    Y_BUTTON     = MD_Y_BUTTON;
    Z_BUTTON     = MD_Z_BUTTON;
    START_BUTTON = MD_START_BUTTON;
    MODE_BUTTON  = MD_MODE_BUTTON;
  break;

  case PAD_TYPE_SFC:
    #if DEBUG_UART_ON
      printf("PAD_TYPE:SFC\r\n");
    #endif
    A_BUTTON     = SFC_A_BUTTON;
    B_BUTTON     = SFC_B_BUTTON;
    C_BUTTON     = SFC_C_BUTTON;
    X_BUTTON     = SFC_X_BUTTON;
    Y_BUTTON     = SFC_Y_BUTTON;
    Z_BUTTON     = SFC_Z_BUTTON;
    START_BUTTON = SFC_START_BUTTON;
    MODE_BUTTON  = SFC_MODE_BUTTON;
  break;

  case PAD_TYPE_PS4:
    #if DEBUG_UART_ON
      printf("PAD_TYPE:PS4\r\n");
    #endif
    A_BUTTON     = PS4_A_BUTTON;
    B_BUTTON     = PS4_B_BUTTON;
    C_BUTTON     = PS4_C_BUTTON;
    X_BUTTON     = PS4_X_BUTTON;
    Y_BUTTON     = PS4_Y_BUTTON;
    Z_BUTTON     = PS4_Z_BUTTON;
    START_BUTTON = PS4_START_BUTTON;
    MODE_BUTTON  = PS4_MODE_BUTTON;
  break;

  case PAD_TYPE_PS4FG:
    #if DEBUG_UART_ON
      printf("PAD_TYPE:PS4 FIGHTING COMMANDER\r\n");
    #endif
    A_BUTTON     = PS4FC_A_BUTTON;
    B_BUTTON     = PS4FC_B_BUTTON;
    C_BUTTON     = PS4FC_C_BUTTON;
    X_BUTTON     = PS4FC_X_BUTTON;
    Y_BUTTON     = PS4FC_Y_BUTTON;
    Z_BUTTON     = PS4FC_Z_BUTTON;
    START_BUTTON = PS4FC_START_BUTTON;
    MODE_BUTTON  = PS4FC_MODE_BUTTON;
  break;

  case PAD_TYPE_XBOX:
    #if DEBUG_UART_ON
      printf("PAD_TYPE:XBOX360\r\n");
    #endif
    A_BUTTON     = XBOX_A_BUTTON;
    B_BUTTON     = XBOX_B_BUTTON;
    C_BUTTON     = XBOX_C_BUTTON;
    X_BUTTON     = XBOX_X_BUTTON;
    Y_BUTTON     = XBOX_Y_BUTTON;
    Z_BUTTON     = XBOX_Z_BUTTON;
    START_BUTTON = XBOX_START_BUTTON;
    MODE_BUTTON  = XBOX_MODE_BUTTON;
  break;

  case PAD_TYPE_XBOXFG:
    #if DEBUG_UART_ON
      printf("PAD_TYPE:XBOX360 FIGHTING COMMANDER\r\n");
    #endif
    A_BUTTON     = XBOXFC_A_BUTTON;
    B_BUTTON     = XBOXFC_B_BUTTON;
    C_BUTTON     = XBOXFC_C_BUTTON;
    X_BUTTON     = XBOXFC_X_BUTTON;
    Y_BUTTON     = XBOXFC_Y_BUTTON;
    Z_BUTTON     = XBOXFC_Z_BUTTON;
    START_BUTTON = XBOXFC_START_BUTTON;
    MODE_BUTTON  = XBOXFC_MODE_BUTTON;
  break;

  default: 
    #if DEBUG_UART_ON
      printf("Unknown\r\n");
    #endif
  break;
  }
}

// ボタン配置の自動判定
void detect_button_config()
{
  // ボタンコンフィグ判定が必要なら呼び出す
  // 初回のレポートのみ実行
  if (need_detect_button_config) {

    enum PAD_TYPE pad_type = PAD_TYPE_UNKNOWN;

    // VID/PIDでの判定
    // 対応を増やしたい場合、
    // pad_config_list に追加する
    const pad_foncig_def_t* l = pad_config_list;
    for( int i=0; i < pad_config_list_count; ++i,++l ) {
      if( (l->vid == device_vid) && (l->pid == device_pid) ) {
        pad_type = l->pad_type;
        #if DEBUG_UART_ON
          #if ENABLE_PAD_NAME
            printf("Detect Gamepad : VID = %04X, PID = %04X \"%s\"\n", device_vid, device_pid, l->pad_name );
          #else
            printf("Detect Gamepad : VID = %04X, PID = %04X\n", device_vid, device_pid);
          #endif
        #endif
        break;
      }
    }

    need_detect_button_config = false;
    change_button_config(pad_type);
  }
}

// --------------------------------------------------------------------
#if MSX_SEL_LOGIC == 0
  #define MSX_SEL_H_def true
  #define MSX_SEL_L_def false
#else
  #define MSX_SEL_H_def false
  #define MSX_SEL_L_def true
#endif
static bool volatile MSX_SEL_H = MSX_SEL_H_def;
static bool volatile MSX_SEL_L = MSX_SEL_L_def;

// --------------------------------------------------------------------
// Report Descriptaor Global Collection Table
typedef struct RD_COLLECTION_TABLE {
  uint8_t   type_id;
  uint16_t  usage_page; // コレクション開始時の値
  uint16_t  usage;      // コレクション開始時の値
  // 他のグループ情報は一旦管理しない
} rd_collection_table;

// Report Descriptaor Global Item Table
typedef struct RD_GLOBAL_TABLE {
  uint16_t  usage_page;     //*need*
  uint8_t   report_size;    //*need*
  uint8_t   report_count;   //*need*
  int32_t   logical_min;    //*need*
  int32_t   logical_max;    //*need*
//int32_t     physical_min;
//int32_t     physical_max;
  int8_t    unit_exponent;  // for 物理単位の指数 (-8 ~ 7)
  uint8_t   unit;           // for 物理単位 (0 ~ 7)
  uint8_t   report_id;
} rd_global_table_t;

// report count = usage array count
enum { rdl_usage_count_max = 32 };

// Report Descriptaor Local Item Table
typedef struct RD_LOCAL_TABLE {
  uint16_t  usage[rdl_usage_count_max];
  uint16_t  usage_count;
  uint16_t  usage_min;
  uint16_t  usage_max;
//uint16_t    designator_index;
//uint16_t    designator_min;
//uint16_t    designator_max;
//uint16_t    string_index;
//uint16_t    string_min;
//uint16_t    string_max;
} rd_local_table_t;


// レポートアイテムの構成情報
typedef struct JOYPAD_REPORT_ITEM
{
  enum JOYPAD_ITEM_ID item_id;  // データ要素の種類
  uint8_t  byte_index;          // レポートバイトストリーム中の該当データ出現位置
  uint8_t  bit_shift;           // LSBからビット出現位置に戻すためのビットシフト
  uint16_t bit_mask;            // LSBにシフトしたビットマスク
  int16_t  logical_min;         // 論理値(RAW値)最小値
  int16_t  logical_max;         // 論理値(RAW値)最大値
} joypad_report_item_t;

// レポート単位の情報
typedef struct JOYPAD_REPORT_INFO
{
  uint8_t  report_id;   // レポートID
  uint8_t  usage;       // Usage ID
  uint16_t usage_page;  // Usage Page ID
  hid_report_type_t report_type; // HID_REPORT_TYPE_???

  joypad_report_item_t items[joyitem_count];  // レポートアイテムの構成情報

  // TODO still use the endpoint size for now
//  uint8_t in_len;      // length of IN report
//  uint8_t out_len;     // length of OUT report
} joypad_report_info_t;


// RI_MAIN_INPUT で アイテムメンバーを登録
// レポートディスクリプタの情報テーブルを使用する
int joypad_add_report_item(
  joypad_report_info_t* info,
  rd_global_table_t const* gtable,
  rd_local_table_t const* ltable,
  uint8_t input_flags,  // RI_MAIN_INPUT に付随するビットフラグ
  uint16_t* p_bit_index
)
{
  int item_count = 0;

  assert(info);
  assert(gtable);
  assert(ltable);
  assert(p_bit_index);

  int bit_index = *p_bit_index;

  for (int i = 0; i < rdl_usage_count_max; ++i )
  {
    joypad_report_item_t* item = 0;
    int usage = 0;

    if (ltable->usage_count) {
      // 出現順にusageを処理する
      if (ltable->usage_count <= i) break;
      usage = ltable->usage[i];
    } else 
    if (i < gtable->report_count)
    {
      // usage_countが0の場合、usage_min ~ usage_max を使用する
      usage = MIN( ltable->usage_min + i, ltable->usage_max);
    }
    else
    {
      break;
    }
    
    switch (gtable->usage_page) {

    // 方向
    case HID_USAGE_PAGE_DESKTOP: {
      switch (usage) {
      case HID_USAGE_DESKTOP_X         : item = &info->items[joyitem_axis_x]; break;
      case HID_USAGE_DESKTOP_Y         : item = &info->items[joyitem_axis_y]; break;
      case HID_USAGE_DESKTOP_Z         : item = &info->items[joyitem_axis_z]; break;
      case HID_USAGE_DESKTOP_RX        : item = &info->items[joyitem_axis_Rx]; break;
      case HID_USAGE_DESKTOP_RY        : item = &info->items[joyitem_axis_Ry]; break;
      case HID_USAGE_DESKTOP_RZ        : item = &info->items[joyitem_axis_Rz]; break;
      case HID_USAGE_DESKTOP_HAT_SWITCH: item = &info->items[joyitem_hat_sw]; break;
      }
    } break;

    // ボタン
    case HID_USAGE_PAGE_BUTTON: {
      // 0は無し→いったん無視
      if ((1 <= usage) && (usage <= joyitem_button_count)) {
        item = &info->items[joyitem_button_1 + usage - 1];
      }
    } break;
    }

    // 該当アイテムなら解析結果テーブルに追加
    if (item) {
      //        input_flags ... 一旦決め打ち                決め打ち設定
      //        *HID_DATA              HID_CONSTANT         データ
      //         HID_ARRAY            *HID_VARIABLE         値
      //        *HID_ABSOLUTE          HID_RELATIVE         絶対値
      //        *HID_WRAP_NO           HID_WRAP             範囲内に丸め込まない
      //        *HID_LINEAR            HID_NONLINEAR        線形
      //        *HID_PREFERRED_STATE   HID_PREFERRED_NO     優先
      //         HID_NO_NULL_POSITION  HID_NULL_STATE        *hat_switchはNULLがある（NULL=範囲外の値）
      //        *HID_NON_VOLATILE      HID_VOLATILE         NONVOLATILE
      //        *HID_BITFIELD          HID_BUFFERED_BYTES   ビット単位フィールド

      item->byte_index = bit_index >> 3; // bit_index /8;
      item->bit_shift = bit_index & 7;
      item->bit_mask = ((uint32_t)1 << gtable->report_size) - 1;

      item->logical_min = gtable->logical_min;
      item->logical_max = gtable->logical_max;

      ++item_count;
    }

    // 次の位置へ
    bit_index += gtable->report_size;
  }

  *p_bit_index = bit_index;
  return item_count;
}

// reportデータからアイテムを取り出す
uint32_t get_report_item_value_( uint8_t const* report, uint16_t report_len, joypad_report_item_t const* item )
{
  if ( !item->bit_mask ) return 0;

  uint32_t const mask = item->bit_mask << item->bit_shift;
  int const bytes = //( mask > 0xffffff ) ? 4 : // 24bit境界を越える item->bit_maskが16bitの場合は不要
                    ( mask > 0xffff   ) ? 3 :   // 16bit境界を越える
                    ( mask > 0xff     ) ? 2 :   // 8bit境界を越える
                    1;
  int index = item->byte_index;
  uint32_t dat = 0;
  for (int i =  0; (i < bytes) && (index < report_len); ++i) {
    dat = (dat << 8) | report[index++];
  }
  uint32_t v = (dat & mask) >> item->bit_shift;
  return v;
}

// レポートデータのアイテム定義を取得
joypad_report_item_t* get_report_item_info( joypad_report_info_t* info, enum JOYPAD_ITEM_ID const item_num )
{
  if ( item_num < 0 ) return 0;
  if ( joyitem_count <= item_num ) return 0;
  joypad_report_item_t * item = &info->items[item_num];
  if ( !item->bit_mask ) return 0;
  return item;
}

// レポートデータのボタンアイテム定義を取得
// button_no = 1 ~ 16
joypad_report_item_t* get_report_button_info( joypad_report_info_t* info, uint8_t button_no )
{
  if ( button_no < 1 ) return 0;
  if ( joyitem_button_count < button_no ) return 0;
  joypad_report_item_t * item = &info->items[joyitem_button_1 + button_no - 1];
  if ( !item->bit_mask ) return 0;
  return item;
}

// reportデータからアイテムを取り出す
uint32_t get_report_item_value( uint8_t const* report, uint16_t report_len, joypad_report_info_t* info, enum JOYPAD_ITEM_ID const item_num )
{
  joypad_report_item_t * item = get_report_item_info( info, item_num );
  if (!item) return 0;
  return get_report_item_value_( report, report_len, item );
}

// reportデータを2値ボタンとしてチェック（trueかfalseで返す）
// 符号付データの場合マイナスでもプラスでもtrueを返す（符号なしにダイナミックキャストして扱うので）
bool check_report_button( uint8_t const* report, uint16_t report_len, joypad_report_info_t* info, enum JOYPAD_ITEM_ID const item_num )
{
  joypad_report_item_t* item = get_report_button_info( info, item_num );
  if ( !item ) return false;

  uint16_t v = get_report_item_value_( report, report_len, item );
  if( 1 == item->bit_mask ) return (v == item->bit_mask);

  const uint16_t threshold = (item->logical_max - item->logical_min) / 2; // 一旦半分以上かで判断
  const int16_t diff = v - item->logical_min;
  return (threshold <= diff);
}

// --------------------------------------------------------------------

#if 0
// --------------------------------------------------------------------
typedef struct TU_ATTR_PACKED {
  uint8_t               x;                      //< X position of the gamepad. LEFT:0 ... CENTER:128 ... RIGHT:255
  uint8_t               y;                      //< Y position of the gamepad. TOP:0 .... CENTER:128 ... BOTTOM:255
  uint32_t      buttons;        //< Buttons of the gamepad.
  int8_t                reserved1;
  int8_t                reserved2;
} my_hid_joystick_report_t;

typedef struct {
  uint8_t               id;                     //      0x01
  uint8_t               notuse_1;       //      0x7F
  uint8_t               notuse_2;       //      0x7F
  uint8_t               x;                      //< X position of the gamepad. LEFT:0 ... CENTER:128 ... RIGHT:255
  uint8_t               y;                      //< Y position of the gamepad. TOP:0 .... CENTER:128 ... BOTTOM:255     
  uint8_t               buttons0;       //< Buttons of the gamepad. : XABY1111
  uint8_t               buttons1;       //< Buttons of the gamepad. : 00SM00CZ
  uint8_t               notuse_7;       //      0x00
} my_hid_megadrive_mini_pad_report_t;
#endif

// --------------------------------------------------------------------
static uint8_t volatile joymega_matrix[5] = {
  0x33, 0x3F, 0x03, 0x3F, 0x3F
};

// --------------------------------------------------------------------
#define MAX_REPORT  4

typedef joypad_report_info_t  report_info_t;

// Each HID instance can has multiple reports
static struct {
  uint8_t report_count;
  report_info_t report_info[MAX_REPORT];
} hid_info[ CFG_TUH_HID ];

static int process_mode = 0;    //      0: joypad_mode, 1: mouse_mode

// --------------------------------------------------------------------
//      Mouse information

//      USBマウスから送られてくる情報を収集するための変数
static volatile int16_t mouse_delta_x = 0;
static volatile int16_t mouse_delta_y = 0;
static volatile int     mouse_resolution = 0;
static int32_t  mouse_button = 0;

//      USBマウスから送られてきた情報を元に「送信用」に加工した値を格納する変数
static volatile int32_t mouse_current_data = 3;
static volatile bool mouse_consume_data = false;

//      現在MSXへ送信している内容を保持する変数
static int32_t  mouse_sending_data = 0;

//      LED Pattern
static int led_state = 0;
static const int led_pattern[7][8] = {
  { 1, 0, 0, 0, 0, 0, 0, 0 },                   //      Joypad mode(wait)
  { 1, 0, 1, 0, 1, 0, 1, 0 },                   //      Joypad mode(detecting)
  { 1, 1, 1, 1, 1, 1, 1, 0 },                   //      Joypad mode(on use)
  { 1, 0, 1, 0, 0, 0, 0, 0 },                   //      Mouse mode (normal)
  { 1, 0, 1, 0, 1, 0, 0, 0 },                   //      Mouse mode (V half)
  { 1, 0, 1, 0, 0, 0, 1, 0 },                   //      Mouse mode (normal2)
  { 1, 1, 0, 1, 0, 1, 0, 0 },                   //      Mouse mode (V half2)
};

// --------------------------------------------------------------------
static void initialization( void ) {
  uint8_t i;

  board_init();
  tusb_init();

  //    GPIOの信号の向きを設定
  for( i = 0; i < 6; i++ ) {
    gpio_init( MSX_BUTTON_PIN + i );
    gpio_set_dir( MSX_BUTTON_PIN + i, GPIO_OUT );
  }
  gpio_init( MSX_SEL_PIN );
  gpio_set_dir( MSX_SEL_PIN, GPIO_IN );
  gpio_pull_up( MSX_SEL_PIN );

  // GPIO ジャンパ 14(+3.3V) -> 15(pull up) 検査準備
  gpio_init( MD_SEL_PIN_O );
  gpio_set_dir( MD_SEL_PIN_O, GPIO_OUT );
  gpio_put( MD_SEL_PIN_O, true );
  gpio_init( MD_SEL_PIN_I );
  gpio_set_dir( MD_SEL_PIN_I, GPIO_IN );
  gpio_pull_down( MD_SEL_PIN_I );
}

// --------------------------------------------------------------------
static uint64_t inline my_get_us( void ) {
  return to_us_since_boot( get_absolute_time() );
}

// --------------------------------------------------------------------
//static bool md_mode = MSX_SEL_LOGIC;
static void check_logic()
{
  bool rev = gpio_get( MD_SEL_PIN_I );
  //md_mode = MSX_SEL_LOGIC ^ rev;
  if (rev) {
    MSX_SEL_L = !MSX_SEL_L_def;
    MSX_SEL_H = !MSX_SEL_H_def;
  } else {
    MSX_SEL_L = MSX_SEL_L_def;
    MSX_SEL_H = MSX_SEL_H_def;
  }
}


// --------------------------------------------------------------------
static void joypad_mode( void ) {
  static const uint32_t mask = 0x3F << MSX_BUTTON_PIN;
  static const uint64_t sequence_trigger_us = 1100;             //      1100[usec]
  static const uint64_t sequence_finish_us = 1600;              //      1600[usec]
  static uint64_t start_time;

  //                b5,b4,b3,b2,b1,b0
  //    matrix[0] = 上 下 Ｌ Ｌ Ａ Ｓ
  //    matrix[1] = 上 下 左 右 Ｂ Ｃ
  //    matrix[2] = Ｌ Ｌ Ｌ Ｌ Ａ Ｓ
  //    matrix[3] = Ｚ Ｙ Ｘ Ｍ Ｈ Ｈ
  //    matrix[4] = Ｈ Ｈ Ｈ Ｈ Ａ Ｓ

  check_logic();

  //    state 0
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_L ) {
    gpio_put_masked( mask, (uint32_t)joymega_matrix[1] << MSX_BUTTON_PIN );
  }
  start_time = my_get_us();

  //    state 1
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_H ) {
    gpio_put_masked( mask, (uint32_t)joymega_matrix[0] << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > sequence_trigger_us ) {
      break;
    }
  }
  if( (my_get_us() - start_time) > sequence_trigger_us ) {
    return;
  }

  //    state 2
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_L ) {
    gpio_put_masked( mask, (uint32_t)joymega_matrix[1] << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > sequence_trigger_us ) {
      break;
    }
  }
  if( (my_get_us() - start_time) > sequence_trigger_us ) {
    return;
  }
  //    state 3
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_H ) {
    gpio_put_masked( mask, (uint32_t)joymega_matrix[0] << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > sequence_trigger_us ) {
      break;
    }
  }
  if( (my_get_us() - start_time) > sequence_trigger_us ) {
    return;
  }
  //    state 4
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_L ) {
    gpio_put_masked( mask, (uint32_t)joymega_matrix[1] << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > sequence_trigger_us ) {
      break;
    }
  }
  if( (my_get_us() - start_time) > sequence_trigger_us ) {
    return;
  }
  //    state 5
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_H ) {
    gpio_put_masked( mask, (uint32_t)joymega_matrix[2] << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > sequence_finish_us ) {
      break;
    }
  }
  if( (my_get_us() - start_time) > sequence_finish_us ) {
    return;
  }
  //    state 6
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_L ) {
    gpio_put_masked( mask, (uint32_t)joymega_matrix[3] << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > sequence_finish_us ) {
      break;
    }
  }
  if( (my_get_us() - start_time) > sequence_finish_us ) {
    return;
  }
  //    state 7
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_H ) {
    gpio_put_masked( mask, (uint32_t)joymega_matrix[4] << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > sequence_finish_us ) {
      break;
    }
  }
}

// --------------------------------------------------------------------
static uint32_t inline get_mouse_button_bits( void ) {
  return (mouse_sending_data & 3);
}

// --------------------------------------------------------------------
static uint32_t inline get_mouse_nibble_bits_1st( void ) {

  //    MSXへ送っている最中に更新されないようにコピーする
  mouse_sending_data = mouse_current_data;

  //    1個目のデータは無意味 (ボタンのみ)
  return get_mouse_button_bits();
}

// --------------------------------------------------------------------
static uint32_t inline get_mouse_nibble_bits_2nd( void ) {

  return get_mouse_button_bits() | ((mouse_sending_data >> 2) & 0x3C);
}

// --------------------------------------------------------------------
static uint32_t inline get_mouse_nibble_bits_3rd( void ) {

  return get_mouse_button_bits() | ((mouse_sending_data >> 6) & 0x3C);
}

// --------------------------------------------------------------------
static uint32_t inline get_mouse_nibble_bits_4th( void ) {

  return get_mouse_button_bits() | ((mouse_sending_data >> 10) & 0x3C);
}

// --------------------------------------------------------------------
static uint32_t inline get_mouse_nibble_bits_5th( void ) {

  return get_mouse_button_bits() | ((mouse_sending_data >> 14) & 0x3C);
}

// --------------------------------------------------------------------
static uint32_t inline get_mouse_nibble_bits_6th( void ) {

  return get_mouse_button_bits();
}

// --------------------------------------------------------------------
static void mouse_mode( void ) {
  static const uint32_t mask = 0x3F << MSX_BUTTON_PIN;
  static const uint64_t timeout_us = 500;               //      500[usec]
  static uint64_t start_time;

  //    idle
  gpio_put_masked( mask, get_mouse_nibble_bits_1st() << MSX_BUTTON_PIN );
  if( gpio_get( MSX_SEL_PIN ) == MSX_SEL_L ) {
    return;
  }

  mouse_consume_data = true;
  mouse_current_data &= 0xF;
  start_time = my_get_us();

  //    state 1
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_H ) {
    gpio_put_masked( mask, get_mouse_nibble_bits_2nd() << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > timeout_us ) {
      return;
    }
  }

  //    state 2
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_L ) {
    gpio_put_masked( mask, get_mouse_nibble_bits_3rd() << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > timeout_us ) {
      return;
    }
  }

  //    state 3
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_H ) {
    gpio_put_masked( mask, get_mouse_nibble_bits_4th() << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > timeout_us ) {
      return;
    }
  }

  //    state 4
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_L ) {
    gpio_put_masked( mask, get_mouse_nibble_bits_5th() << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > timeout_us ) {
      return;
    }
  }

  //    state 5
  while( gpio_get( MSX_SEL_PIN ) == MSX_SEL_H ) {
    gpio_put_masked( mask, get_mouse_nibble_bits_6th() << MSX_BUTTON_PIN );
    if( (my_get_us() - start_time) > timeout_us ) {
      return;
    }
  }
}

// --------------------------------------------------------------------
void response_core( void ) {

  for( ;; ) {
    if( process_mode == 0 ) {
      joypad_mode();
    }
    else {
      mouse_mode();
    }
  }
}

//--------------------------------------------------------------------+
void led_blinking_task(void) {
  const uint32_t interval_ms = 250;
  static uint32_t start_ms = 0;

  // Blink every interval ms
  if (board_millis() - start_ms < interval_ms) return; // not enough time
  start_ms += interval_ms;
  if( process_mode == 0 ) {
    board_led_write( led_pattern[ gamepad_poc_step + 0 ][ led_state ] );
  }
  else {
    board_led_write( led_pattern[ mouse_resolution + 3 ][ led_state ] );
  }
  led_state = (led_state + 1) & 7;
}

// --------------------------------------------------------------------
static void process_gamepad_report( uint8_t const *report, uint16_t len, report_info_t *info ) {
  static const uint8_t default_matrix[5] = {
    0x33, 0x3F, 0x03, 0x3F, 0x3F
  };
  uint8_t matrix[5];

  #if DEBUG_UART_ON
  #if DEBUG_USE_ANALYSIS > 1
    printf( "process_gamepad_report()\n" );
  #endif
  #endif

  // ゲームパッド認識状況を「動作中」にセット
  if (gamepad_poc_step == 1) gamepad_poc_step = 2;

  // 必要ならボタン配置調整
  if (need_detect_button_config) {
    detect_button_config();
  }

  //                b5,b4,b3,b2,b1,b0
  //    matrix[0] = 上 下 Ｌ Ｌ Ａ Ｓ
  //    matrix[1] = 上 下 左 右 Ｂ Ｃ
  //    matrix[2] = Ｌ Ｌ Ｌ Ｌ Ａ Ｓ
  //    matrix[3] = Ｚ Ｙ Ｘ Ｍ Ｈ Ｈ
  //    matrix[4] = Ｈ Ｈ Ｈ Ｈ Ａ Ｓ

  memcpy( matrix, default_matrix, sizeof(matrix) );

  joypad_report_item_t* item = 0;

  // x-axis
  joypad_report_item_t* x_item =
  item = get_report_item_info( info, joyitem_axis_x );
  uint32_t x = get_report_item_value_( report, len, item );
  if (item) {
    uint32_t v = x;
    uint32_t range = item->logical_max - item->logical_min + 1;
    uint32_t center = range / 2;
    uint32_t threshold = range / 8;
    // 左
    if ( v <= (center - threshold) ) {
      matrix[1] &= 0x37;
    } else
    // 右
    if ( v >= (center + threshold) ) {
      matrix[1] &= 0x3B;
  }
  }

  // y-axis
  joypad_report_item_t* y_item =
  item = get_report_item_info( info, joyitem_axis_y );
  uint32_t y = get_report_item_value_( report, len, item );
  if (item) {
    uint32_t v = y;
    uint32_t range = item->logical_max - item->logical_min + 1;
    uint32_t center = range / 2;
    uint32_t threshold = range / 8;
    // 上
    if ( v <= (center - threshold) ) {
      matrix[0] &= 0x1F;
      matrix[1] &= 0x1F;
    } else
    // 下
    if ( v >= (center + threshold) ) {
      matrix[0] &= 0x2F;
      matrix[1] &= 0x2F;
  }
  }

  // hat-switch
  // （上を0度とした時計回りの角度）
  // （論理デジタル値の角度分解能はデバイスにより異なるので対応する）
  joypad_report_item_t* hat_item =
  item = get_report_item_info( info, joyitem_hat_sw );
  uint32_t hat = get_report_item_value_( report, len, item );
  if (item) {
    uint32_t v = hat;
    uint32_t range = item->logical_max - item->logical_min + 1;
    if ( v <= item->logical_max ) {

      // 16段階以上にする
      if ( range <= 4 ) {
        range *= 4;
        v *= 4;
      } else
      if ( range <= 8 ) {
        range *= 2;
        v *= 2;
      }

      // 左
      if (( v > range * 9 / 16 ) && ( v < range * 15 / 16 )) {
        matrix[1] &= 0x37;
      }
      // 右
      if (( v > range * 1 / 16 ) && ( v < range * 7 / 16 )) {
        matrix[1] &= 0x3B;
      }
      // 上
      if (( v < range * 3 / 16 ) || ( v > range * 13 / 16 )) {
        matrix[0] &= 0x1F;
        matrix[1] &= 0x1F;
      }
      // 下
      if (( v > range * 5 / 16 ) && ( v < range * 11 / 16 )) {
        matrix[0] &= 0x2F;
        matrix[1] &= 0x2F;
      }
    }
  }

  // check_report_buttonは入力をONかOFFで
  // 符号付データの場合マイナスでもプラスでもONを返す
  if( check_report_button( report, len, info, A_BUTTON) ) {
    matrix[0] &= 0x3D;
    matrix[2] &= 0x3D;
    matrix[4] &= 0x3D;
  }
  if( check_report_button( report, len, info, B_BUTTON) ) {
    matrix[1] &= 0x3D;
  }
  if( check_report_button( report, len, info, C_BUTTON) ) {
    matrix[1] &= 0x3E;
  }
  if( check_report_button( report, len, info, X_BUTTON) ) {
    matrix[3] &= 0x37;
  }
  if( check_report_button( report, len, info, Y_BUTTON) ) {
    matrix[3] &= 0x2F;
  }
  if( check_report_button( report, len, info, Z_BUTTON) ) {
    matrix[3] &= 0x1F;
  }
  if( check_report_button( report, len, info, START_BUTTON) ) {
    matrix[0] &= 0x3E;
    matrix[2] &= 0x3E;
    matrix[4] &= 0x3E;
  }
  if( check_report_button( report, len, info, MODE_BUTTON) ) {
    matrix[3] &= 0x3B;
  }
  memcpy( (void*) joymega_matrix, matrix, sizeof(matrix) );

  #if DEBUG_UART_ON
  #if DEBUG_USE_ANALYSIS > 1
    if (x_item) printf( "pos_x = %d\r\n", (int)x );
    if (y_item) printf( "pos_y = %d\r\n", (int)y );
    if (hat_item) printf( "hat = %d\r\n", (int)hat );
    printf( "buttons = ");
    for ( int i = 1; i <= joyitem_button_count; ++i ) {
      joypad_report_item_t const*
      item = get_report_button_info( info, i );
      if (!item) {
        printf("-");
      } else 
      if (get_report_item_value_( report, len, item )) {
        printf("1");
      } else {
        printf("0");
      }
    }
    printf( "\r\n" );
  #endif
  #endif
}

// --------------------------------------------------------------------
static void process_mouse_report( hid_mouse_report_t const * report ) {
  int16_t delta_x;
  int16_t delta_y;
  int32_t send_data, last_mouse_button;
  int d1, d2, d3, d4;
  static const int reverse_inv4[] = { 3, 1, 2, 0 };
  static const int reverse16[] = { 0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15 };
  
  if( mouse_consume_data ) {
    mouse_consume_data = false;
    mouse_delta_x = 0;
    mouse_delta_y = 0;
  }
  delta_x = mouse_delta_x - (int16_t) report->x;
  if( delta_x < -127 ) {
    delta_x = -127;
  }
  else if( delta_x > 127 ) {
    delta_x = 127;
  }

  delta_y = mouse_delta_y - (int16_t) report->y;
  if( delta_y < -127 ) {
    delta_y = -127;
  }
  else if( delta_y > 127 ) {
    delta_y = 127;
  }

  last_mouse_button = mouse_button;
  mouse_button = (report->buttons & (MOUSE_BUTTON_RIGHT | MOUSE_BUTTON_LEFT | MOUSE_BUTTON_MIDDLE));

  //    中ボタンが押されたら解像度を変える
  if( !(last_mouse_button & MOUSE_BUTTON_MIDDLE) && (mouse_button & MOUSE_BUTTON_MIDDLE) ) {
    mouse_resolution = (mouse_resolution + 1) & 3;
  }

  //    送信用データを作る
  send_data = reverse_inv4[ mouse_button & 3 ];
  switch( mouse_resolution ) {
  default:
  case 0:
    d1 = reverse16[((delta_x     ) >> 4) & 0x0F ];
    d2 = reverse16[ (delta_x     )       & 0x0F ];
    d3 = reverse16[((delta_y     ) >> 4) & 0x0F ];
    d4 = reverse16[ (delta_y     )       & 0x0F ];
    break;
  case 1:
    d1 = reverse16[((delta_x     ) >> 4) & 0x0F ];
    d2 = reverse16[ (delta_x     )       & 0x0F ];
    d3 = reverse16[((delta_y >> 1) >> 4) & 0x0F ];
    d4 = reverse16[ (delta_y >> 1)       & 0x0F ];
    break;
  case 2:
    d1 = reverse16[((delta_x >> 1) >> 4) & 0x0F ];
    d2 = reverse16[ (delta_x >> 1)       & 0x0F ];
    d3 = reverse16[((delta_y >> 1) >> 4) & 0x0F ];
    d4 = reverse16[ (delta_y >> 1)       & 0x0F ];
    break;
  case 3:
    d1 = reverse16[((delta_x >> 1) >> 4) & 0x0F ];
    d2 = reverse16[ (delta_x >> 1)       & 0x0F ];
    d3 = reverse16[((delta_y >> 2) >> 4) & 0x0F ];
    d4 = reverse16[ (delta_y >> 2)       & 0x0F ];
    break;
  }
  send_data = send_data | (d1 << 4) | (d2 << 8) | (d3 << 12) | (d4 << 16);

  //    排他制御は面倒なので省略 (^^;
  mouse_delta_x = delta_x;
  mouse_delta_y = delta_y;
  mouse_current_data = send_data;
}

// --------------------------------------------------------------------
int main(void) {

  initialization();
  multicore_launch_core1( response_core );

  #if DEBUG_UART_ON
    printf("USB Gamepad bridge for MSX ver.%s\r\n", USB_FAMEPAD_BRIDGE_FOR_MSX_VERSION);
  #endif

  for( ;; ) {
    tuh_task();
    led_blinking_task();
  }
  return 0;
}

// --------------------------------------------------------------------
//      [DEBUG]
// --------------------------------------------------------------------
#if DEBUG_USE_ANALYSIS
void debug_dump_hex( uint8_t const* dat, uint16_t dat_len )
{
  #if DEBUG_UART_ON
  for (uint16_t i = 0; i < dat_len; ++i)
  {
    printf( "%02X ", dat[i] );
    if ( (i & 15) == 15 ) {
      printf( "\n" );
    }
  }
  if ( dat_len & 15 ) {
    printf( "\n" );
  }
  return;
  #endif//#if DEBUG_UART_ON
}
#endif//#if DEBUG_USE_ANALYSIS

//--------------------------------------------------------------------+
// Report Item Types 不足分の対応
//--------------------------------------------------------------------+
enum {
//  RI_TYPE_MAIN   = 0,
//  RI_TYPE_GLOBAL = 1,
//  RI_TYPE_LOCAL  = 2,
  RI_TYPE_LONGITEM  = 3,
};

//--------------------------------------------------------------------+
// Report Descriptor Parser
// 対策版
//--------------------------------------------------------------------+
uint8_t joypad_hid_parse_report_descriptor(joypad_report_info_t* report_info_arr, uint8_t arr_count, uint8_t const* desc_report, uint16_t desc_len)
{
  #if DEBUG_UART_ON
  #if DEBUG_USE_ANALYSIS 
    printf("joypad_hid_parse_report_descriptor();\r\n");
  #endif
  #endif
  // ビットフィールドは移植性が低いのでバイナリ解析に使用する事は推奨されない
  // どうしても使いたいならコンパイラ依存のpackedオプションを使用する
  // Report Item 6.2.2.2 USB HID 1.11
  union TU_ATTR_PACKED
  {
    uint8_t byte;
    struct TU_ATTR_PACKED
    {
    uint8_t size : 2;
    uint8_t type : 2;
    uint8_t tag  : 4;
    };
  } header;

  // Global Item
  enum { ri_global_stack_size = 8       };
  uint8_t ri_global_stack_depth = 0;
  rd_global_table_t ri_global_stack[ ri_global_stack_size ];
  rd_global_table_t ri_global;
  tu_memclr(ri_global_stack, sizeof(ri_global_stack));
  tu_memclr(&ri_global, sizeof(ri_global));

  // Local Item
  rd_local_table_t ri_local;
  tu_memclr(&ri_local, sizeof(ri_local));

  //
  tu_memclr(report_info_arr, arr_count*sizeof(report_info_t));

  uint8_t report_num = 1;
  report_info_t* info = report_info_arr;

  // current parsed report count & size from descriptor
//  uint8_t ri_report_count = 0;
//  uint8_t ri_report_size = 0;

  enum { ri_collection_depth_max = 8 };
  uint8_t ri_collection_depth = 0;
  rd_collection_table ri_collection[ ri_collection_depth_max ];
  tu_memclr(ri_collection, sizeof(ri_collection));
  
  uint8_t rd_collection_idx_apprication = 0;  //HID_COLLECTION_APPLICATIONがあるコレクション階層

  uint16_t bit_index = 0;

  while(desc_len && report_num < arr_count)
  {
    header.byte = *desc_report++;
    desc_len--;

    uint8_t const tag  = header.tag;
    uint8_t const type = header.type;
    uint8_t size =  (1 << header.size) >> 1;

    uint32_t u32data = desc_report[0];
    if (size > 1 ) u32data |= desc_report[1] << 8;
    if (size > 2 ) u32data |= (desc_report[2] << 16) | (desc_report[3] << 24);
    int32_t s32data = *(int32_t*)&u32data;

    #if DEBUG_UART_ON
    #if DEBUG_USE_ANALYSIS > 2
      printf( "tag = %d, type = %d, size = %d", tag, type, size);
      if( size ) {
        printf(", data = ");
        for(uint32_t i=0; i<size; i++) printf("%02X ", desc_report[i]);
      }
      printf("\r\n");
    #endif
    #endif

    switch(type)
    {
      case RI_TYPE_MAIN: {
        bool need_clear_local = true;
        switch (tag)
        {
          case RI_MAIN_INPUT:
            if (info->report_id && ri_global.report_id && 
                (info->report_id != ri_global.report_id)) 
            {
              info++;
              report_num++;
              bit_index = 0;
            }

            if (!info->usage_page) // 0 == UNKNOWN
            {
              assert(rd_collection_idx_apprication);
              info->usage_page = ri_collection[rd_collection_idx_apprication].usage_page;
            }
            if (!info->usage) // 0 == UNKNOWN
            {
              info->usage = ri_collection[rd_collection_idx_apprication].usage;
            }

            info->report_id = ri_global.report_id;
            joypad_add_report_item( info, &ri_global, &ri_local, u32data, &bit_index );
          break;
          case RI_MAIN_OUTPUT: break;
          case RI_MAIN_FEATURE: break;

          case RI_MAIN_COLLECTION:
            if (ri_collection_depth < ri_collection_depth_max) 
            {
              ri_collection_depth++;
              ri_collection[ ri_collection_depth ].type_id = u32data;
              ri_collection[ ri_collection_depth ].usage_page = ri_global.usage_page;
              ri_collection[ ri_collection_depth ].usage = ri_local.usage[ri_local.usage_count ? ri_local.usage_count - 1 : 0];

              if (u32data == HID_COLLECTION_APPLICATION) 
              {
                rd_collection_idx_apprication = ri_collection_depth;
              }
            }
          break;

          case RI_MAIN_COLLECTION_END:
            if (ri_collection_depth)
            {
              ri_collection_depth--;
              if (ri_collection_depth < rd_collection_idx_apprication)
              {
                rd_collection_idx_apprication = 0;
              }
            }
          break;

          default: 
            need_clear_local = false;
          break;
        }
        if (need_clear_local) {
          tu_memclr(&ri_local, sizeof(ri_local));
        }
      }
      break;

      case RI_TYPE_GLOBAL:
        switch(tag)
        {
          case RI_GLOBAL_USAGE_PAGE:
            ri_global.usage_page = u32data;
          break;

          case RI_GLOBAL_LOGICAL_MIN   : 
            ri_global.logical_min = s32data;
          break;

          case RI_GLOBAL_LOGICAL_MAX   : 
            ri_global.logical_max = s32data;
          break;

          case RI_GLOBAL_PHYSICAL_MIN  : 
          //    ri_global.physical_min = s32data;
          break;

          case RI_GLOBAL_PHYSICAL_MAX  : 
          //    ri_global.physical_max = s32data;
          break;

          case RI_GLOBAL_REPORT_ID:
            ri_global.report_id = u32data;
          break;

          case RI_GLOBAL_REPORT_SIZE:
            ri_global.report_size = u32data;
          break;

          case RI_GLOBAL_REPORT_COUNT:
            ri_global.report_count = u32data;
          break;

          case RI_GLOBAL_UNIT_EXPONENT :
            ri_global.unit_exponent = u32data;
          break;

          case RI_GLOBAL_UNIT          :
            ri_global.unit = u32data;
          break;

          case RI_GLOBAL_PUSH          :
            if (ri_global_stack_depth < ri_global_stack_size) {
              ri_global_stack[ri_global_stack_depth++] = ri_global;
            }
          break;

          case RI_GLOBAL_POP           : 
            if (ri_global_stack_depth) {
              ri_global = ri_global_stack[--ri_global_stack_depth];
            }
          break;

          default: break;
        }
      break;

      case RI_TYPE_LOCAL:
        switch(tag)
        {
          case RI_LOCAL_USAGE:
            if (ri_local.usage_count < rdl_usage_count_max) {
              ri_local.usage[ri_local.usage_count++] = u32data;
            }
          break;

          case RI_LOCAL_USAGE_MIN        : 
        ri_local.usage_min = u32data;
      break;

          case RI_LOCAL_USAGE_MAX        :
        ri_local.usage_max = u32data;
      break;

          case RI_LOCAL_DESIGNATOR_INDEX :
      //        ri_local.designator_index = u32data;
      break;

          case RI_LOCAL_DESIGNATOR_MIN   :
      //        ri_local.designator_min = u32data;
      break;

          case RI_LOCAL_DESIGNATOR_MAX   :
      //        ri_local.designator_max = u32data;
      break;

          case RI_LOCAL_STRING_INDEX     :
      //        ri_local.string_index = u32data;
      break;

          case RI_LOCAL_STRING_MIN       :
      //        ri_local.string_min = u32data;
      break;

          case RI_LOCAL_STRING_MAX       :
      //        ri_local.string_max = u32data;
      break;

          case RI_LOCAL_DELIMITER        :
        // RI_LOCAL_DELIMITER(OPEN) - RI_LOCAL_DELIMITER(CLOSE)
      // で囲んだ中に記述したUsageは共用体、別名のような扱いをする
      // TODO: できれば対応
      break;

          default: break;
        }
      break;

    case RI_TYPE_LONGITEM: {
      assert( size == 2 );
      uint8_t const longitem_size = desc_report[ 0 ];
      #if DEBUG_UART_ON
      #if DEBUG_USE_ANALYSIS > 2
        printf("long_item_tag = %d, long_item_size = %d", desc_report[ 1 ], longitem_size);
        if( longitem_size ) {
          printf(", data = ");
          for(uint32_t i=0; i<longitem_size; i++) printf("%02X ", desc_report[ size + i ]);
        }
        printf("\r\n");
      #endif
      #endif

      // 単純にスキップする
      size += longitem_size;
    }
    break;

      // error
      default: break;
    }

    desc_report += size;
    desc_len    -= size;
  }

  #if DEBUG_UART_ON
  #if 1//DEBUG_USE_ANALYSIS
    for ( uint8_t i = 0; i < report_num; i++ )
    {
      info = report_info_arr+i;
      printf("report %u: id = %u, usage_page = %u, usage = %u\r\n", i, info->report_id, info->usage_page, info->usage);
    }
  #endif
  #endif

  return report_num;
}

// --------------------------------------------------------------------
//      HIDが接続されたときに呼び出されるコールバック
//
//      Callback to be called when a gamepad is connected.
//
void tuh_hid_mount_cb( uint8_t dev_addr, uint8_t instance, uint8_t const* desc_report, uint16_t desc_len ) {

  // ボタンコンフィグ判定が必要
  need_detect_button_config = true;

  // Interface protocol (hid_interface_protocol_enum_t)
  uint8_t const itf_protocol = tuh_hid_interface_protocol( dev_addr, instance );
  #if DEBUG_UART_ON
    printf( "tuh_hid_mount_cb( %d, %d, %p, %d );\r\n", dev_addr, instance, desc_report, desc_len );
  #if DEBUG_USE_ANALYSIS > 2
    printf("USB report descriptor: \n");
    printf("------------------------------------------------\n");
    debug_dump_hex( desc_report, desc_len );
    printf("------------------------------------------------\n");
  #endif

    // デバイス固有ID
    tuh_vid_pid_get(dev_addr, &device_vid, &device_pid);
    printf("VID = %04x, PID = %04x\r\n", device_vid, device_pid );
  #endif

  // By default host stack will use activate boot protocol on supported interface.
  // Therefore for this simple example, we only need to parse generic report descriptor (with built-in parser)
  if( itf_protocol == HID_ITF_PROTOCOL_NONE ) {
    #if DEBUG_UART_ON
      printf("HID_ITF_PROTOCOL_NONE\r\n");
    #endif
    hid_info[instance].report_count = joypad_hid_parse_report_descriptor(hid_info[instance].report_info, MAX_REPORT, desc_report, desc_len);
    process_mode = 0;   //      joypad_mode
    // ゲームパッド認識状況を「認識中」にセット
    if (gamepad_poc_step == 0) gamepad_poc_step = 1;
  }
  else if( itf_protocol == HID_ITF_PROTOCOL_MOUSE ) {
    #if DEBUG_UART_ON
      printf("HID_ITF_PROTOCOL_MOUSE\r\n");
    #endif
    process_mode = 1;   //      mouse_mode
    mouse_delta_x = 0;
    mouse_delta_y = 0;
    mouse_button = 0;
    mouse_resolution = 0;
  }
  else {
    process_mode = 0;   //      joypad_mode
  }

  // request to receive report
  // tuh_hid_report_received_cb() will be invoked when report is available
  if( !tuh_hid_receive_report( dev_addr, instance ) ) {
    #if DEBUG_UART_ON
      printf( "Error: cannot request to receive report\r\n" );
    #endif
  }
}

// --------------------------------------------------------------------
//      HIDが切断されたときに呼び出されるコールバック
//
//      Callback to be called when the gamepad is disconnected.
//
void tuh_hid_umount_cb( uint8_t dev_addr, uint8_t instance ) {

  (void) dev_addr;
  (void) instance;
  #if DEBUG_UART_ON
    printf( "tuh_hid_umount_cb( %d, %d );\n", dev_addr, instance );
  #endif

  process_mode = 0;     //      joypad_mode

  device_vid = -1;
  device_pid = -1;
  // ゲームパッド認識状況を「なし」にセット
  gamepad_poc_step = 0;

}

// --------------------------------------------------------------------
void process_generic_report( uint8_t instance, uint8_t const* report, uint16_t len ) {

  #if DEBUG_UART_ON
  #if DEBUG_USE_ANALYSIS > 2
    printf("USB report: \n");
    printf("------------------------------------------------\n");
    debug_dump_hex( report, len );
    printf("------------------------------------------------\n");
  #endif
  #endif
  uint8_t const rpt_count = hid_info[instance].report_count;
  report_info_t* rpt_info_arr = hid_info[instance].report_info;
  report_info_t* rpt_info = NULL;

  if( rpt_count == 1 && rpt_info_arr[0].report_id == 0 ) {
    // Simple report without report ID as 1st byte
    rpt_info = &rpt_info_arr[0];
  }
  else {
    // Composite report, 1st byte is report ID, data starts from 2nd byte
    uint8_t const rpt_id = report[0];

    // Find report id in the arrray
    for( uint8_t i = 0; i < rpt_count; i++ ) {
      if( rpt_id == rpt_info_arr[i].report_id ) {
        rpt_info = &rpt_info_arr[i];
        break;
      }
    }
    report++;
    len--;
  }

  if( rpt_info == NULL ) {
    #if DEBUG_UART_ON
      printf("Couldn't find the report info for this report !\r\n");
    #endif
    return;
  }

  if( rpt_info->usage_page == HID_USAGE_PAGE_DESKTOP ) {
    switch( rpt_info->usage ) {
    case HID_USAGE_DESKTOP_GAMEPAD:
    case HID_USAGE_DESKTOP_JOYSTICK:
      process_gamepad_report( (uint8_t const*) report, len, rpt_info );
      break;
    default:
      printf( "generic usage: %02X\r\n", rpt_info->usage );
      break;
    }
  }
}

// --------------------------------------------------------------------
void tuh_hid_report_received_cb( uint8_t dev_addr, uint8_t instance, uint8_t const* report, uint16_t len ) {

  uint8_t const itf_protocol = tuh_hid_interface_protocol( dev_addr, instance );

  #if DEBUG_UART_ON
  #if DEBUG_USE_ANALYSIS > 1
    printf( "tuh_hid_report_received_cb( %d, %d, %p, %d )\n", dev_addr, instance, report, len );
  #endif
  #endif

  if( itf_protocol == HID_ITF_PROTOCOL_KEYBOARD ) {
    //  none
  }
  else if( itf_protocol == HID_ITF_PROTOCOL_MOUSE ) {
    process_mouse_report( (hid_mouse_report_t const*) report );
  }
  else {
    process_generic_report( instance, report, len );
  }

  // continue to request to receive report
  if( !tuh_hid_receive_report( dev_addr, instance ) ) {
    #if DEBUG_UART_ON
      printf("Error: cannot request to receive report\r\n");
    #endif
  }
}
