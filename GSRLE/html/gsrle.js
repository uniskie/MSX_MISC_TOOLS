const toString = Object.prototype.toString;

const default_log_msg = 
`-使い方-
1. MSX画像ファイルやパレットファイルをドロップ
2. ファイルボタンを押して開く
3. メイン画像を開いた後に、インターレースページ1画像、パレットを追加できる
4. 画像ファイルやパレットは詳細タブに形式を指定保存するボタンがある

- 補足 -
1. グラフサウルス圧縮形式で保存可能 (※ 保存時は表示画面サイズで保存)
2. パレットの有無、画面縦サイズ、圧縮などはデータの内容で判定。
3. SC1はSSCREEN12のインターレース画像として扱う
4. SCREEN1は非対応。SCREEN2～12の画像に対応 (※SCREEN 9は未テスト)
5. ドットアスペクト比 1.133:1 は良く聞く比率。1.177:1 はOpenMSXに近い値`;

// ========================================================
// 初回（自動でアコーディオンタブを閉じる）
let isFirst = true;

// ドラッグアンドドロップ受付状態
let drop_avilable = true;

// 自動保存モード
let quick_save_mode = 'none';
const quick_save_mode_value = 
 ['none', 'bsave_full', 'bsave_mini', 'gsrle_save'];

// ========================================================
// 読み込み済みファイル管理
// ========================================================
function LogFile( file ) {
    return { name: file.name, size: file.size, header: null };
}
const empty_file = { name:'',  size:0 };
let main_file = empty_file;
let sub_file = empty_file;
let pal_file = empty_file;

// ファイル読み込み待ちキュー
var file_load_que = new Array();

// ========================================================
// 動作ログ表示
// ========================================================
let log_string = [];
const log_height = 3;
function add_log( s )
{
    if (log_string.length >= log_height) {
        log_string.shift();
    }
    log_string.push( s );
    log_text.innerText = '' + log_string.join('\n');
}


// ========================================================
// ファイル情報テキスト作成
// ========================================================
function fileText( file ) {
    if (file.header === undefined) {
        return `${file.name} (${file.size}Bytes)`;
    } else {
        if (file.header && file.header.isCompress) {
            return `${file.name}  (GS圧縮 ${file.size}Bytes)`;
        } else {
            return `${file.name} (${file.size}Bytes)`;
        }
    }
}

// ========================================================
// 現在のファイル情報
// ========================================================
function displayCurrentFilename() {
    if (filename_area === undefined) return;

    if (main_file.name.length) {
        filename_area.textContent = fileText(main_file);
        detail_page0_file.textContent = fileText(main_file);
        if (main_file.header) {
            detail_page0_spec.textContent = 
            `[START:0x${main_file.header.start.toString(16)} END:0x${main_file.header.end}]`;
        } else {
            detail_page0_spec.textContent = '';
        }
        page0_save_bsave   .disabled = false;
        page0_save_bsave_np.disabled = false;
        page0_save_gsrle   .disabled = false;
        page0_save_bsave   .style.display ="inline-block";
        page0_save_bsave_np.style.display ="inline-block";
        page0_save_gsrle   .style.display ="inline-block";
    } else {
        filename_area.textContent = '';
        detail_page0_file.textContent = '';
        detail_page0_spec.textContent = '';
        page0_save_bsave   .disabled = true;
        page0_save_bsave_np.disabled = true;
        page0_save_gsrle   .disabled = true;
        page0_save_bsave   .style.display ="none";
        page0_save_bsave_np.style.display ="none";
        page0_save_gsrle   .style.display ="none";
    }

    if (sub_file.name.length) {
        filename_area2.textContent = fileText(sub_file);
        detail_page1_file.textContent = fileText(sub_file);
        if (sub_file.header) {
            detail_page1_spec.textContent = 
            `[START:0x${sub_file.header.start.toString(16)} END:0x${sub_file.header.end}]`;
        } else {
            detail_page1_spec.textContent = '';
        }
        //detail_page1.style.display ="inline-block";
        page1_save_bsave   .disabled = false;
        page1_save_bsave_np.disabled = false;
        page1_save_gsrle   .disabled = false;
        page1_save_bsave   .style.display ="inline-block";
        page1_save_bsave_np.style.display ="inline-block";
        page1_save_gsrle   .style.display ="inline-block";
    } else {
        filename_area2.textContent = '';
        if (vdp.screen_no < 5) {
            detail_page1_file.textContent = '';
            detail_page1_spec.textContent = '[ CHARACTER PATTERN GENERATOR TABLE]';
        } else {
            detail_page1_file.textContent = '';
            detail_page1_spec.textContent = '';
        }
        //detail_page1.style.display ="none";
        page1_save_bsave   .disabled = true;
        page1_save_bsave_np.disabled = true;
        page1_save_gsrle   .disabled = true;
        page1_save_bsave   .style.display ="none";
        page1_save_bsave_np.style.display ="none";
        page1_save_gsrle   .style.display ="none";
    }

    if (pal_file.name.length) {
        filename_area3.textContent = fileText(pal_file);
        detail_pal_file.textContent = fileText(pal_file);
    } else {
        filename_area3.textContent = '';
        detail_pal_file.textContent =  '';
    }

    if (vdp.interlace_mode || (vdp.screen_no < 5)) {
        detail_page1.style.display ="inline-block";
    } else {
        detail_page1.style.display ="none";
    }

    //spec_details

    var s = '[SCREEN ' + vdp.screen_no + "] ";
    s = s + '[' + vdp.mode_info.name + '] ';
    s = s + '[WIDTH ' + vdp.width + '] ';
    s = s + '[HEIGHT ' + vdp.height + '] ';
    if (vdp.interlace_mode) s = s + '[Interlace ON] ';
    spec_details.innerText = s;
}

//================================================
// 拡張子情報
//================================================
function getExt( filename )
{
    return filename.split('.').pop().toUpperCase();
}
function getBasename( filename )
{
    return filename.split('.').shift();
}

// パレット拡張子
const ext_pal = [ 'PL5', 'PL7', 'PLT', 'PAL' ];
function isPaletteFile( ext )
{
    return (-1 < ext_pal.indexOf(ext));
}

// 画像拡張子
// 拡張子でパレットの有無を判定しない
const ext_info = [

    // グラフィック
    {ext:'.SC2', screen_no: 2, interlace:0, page:0, type:0, bsave:'.SC2', gs:'.SR2'},	// BSAVE
	{ext:'.SC3', screen_no: 3, interlace:0, page:0, type:0, bsave:'.SC3', gs:'.SR4'},	// BSAVE
	{ext:'.SC4', screen_no: 4, interlace:0, page:0, type:0, bsave:'.SC4', gs:'.SR3'},	// BSAVE
	{ext:'.SC5', screen_no: 5, interlace:0, page:0, type:0, bsave:'.SC5', gs:'.SR5'},	// BSAVE
	{ext:'.SC6', screen_no: 6, interlace:0, page:0, type:0, bsave:'.SC6', gs:'.SR6'},	// BSAVE
	{ext:'.SC7', screen_no: 7, interlace:0, page:0, type:0, bsave:'.SC7', gs:'.SR7'},	// BSAVE
	{ext:'.SC8', screen_no: 8, interlace:0, page:0, type:0, bsave:'.SC8', gs:'.SR8'},	// BSAVE
	{ext:'.S10', screen_no:10, interlace:0, page:0, type:0, bsave:'.S10', gs:'.SRA'},	// BSAVE
	{ext:'.S12', screen_no:12, interlace:0, page:0, type:0, bsave:'.S12', gs:'.SRC'},	// BSAVE
	{ext:'.SCA', screen_no:10, interlace:0, page:0, type:0, bsave:'.SCA', gs:'.SRA'},	// BSAVE
	{ext:'.SCC', screen_no:12, interlace:0, page:0, type:0, bsave:'.SCC', gs:'.SRC'},	// BSAVE

    {ext:'.S50', screen_no: 5, interlace:1, page:0, type:0, bsave:'.S50', gs:'.R50'},	// BSAVE interlace
    {ext:'.S51', screen_no: 5, interlace:1, page:1, type:0, bsave:'.S51', gs:'.R51'},	// BSAVE interlace
	{ext:'.S60', screen_no: 6, interlace:1, page:0, type:0, bsave:'.S60', gs:'.R60'},	// BSAVE interlace
    {ext:'.S61', screen_no: 6, interlace:1, page:1, type:0, bsave:'.S61', gs:'.R61'},	// BSAVE interlace
	{ext:'.S70', screen_no: 7, interlace:1, page:0, type:0, bsave:'.S70', gs:'.R70'},	// BSAVE interlace
    {ext:'.S71', screen_no: 7, interlace:1, page:1, type:0, bsave:'.S71', gs:'.R71'},	// BSAVE interlace
	{ext:'.S80', screen_no: 8, interlace:1, page:0, type:0, bsave:'.S80', gs:'.R80'},	// BSAVE interlace
    {ext:'.S81', screen_no: 8, interlace:1, page:1, type:0, bsave:'.S81', gs:'.R81'},	// BSAVE interlace
	{ext:'.SA0', screen_no:10, interlace:1, page:0, type:0, bsave:'.SA0', gs:'.RA0'},	// BSAVE interlace
    {ext:'.SA1', screen_no:10, interlace:1, page:1, type:0, bsave:'.SA1', gs:'.RA1'},	// BSAVE interlace
	{ext:'.SC0', screen_no:12, interlace:1, page:0, type:0, bsave:'.SC0', gs:'.RC0'},	// BSAVE interlace
    {ext:'.SC1', screen_no:12, interlace:1, page:1, type:0, bsave:'.SC1', gs:'.RC1'},	// BSAVE interlace

    {ext:'.SR2', screen_no: 2, interlace:0, page:0, type:1, bsave:'.SC2', gs:'.SR2'},	// GRAPH SAURUS
	{ext:'.SR4', screen_no: 3, interlace:0, page:0, type:1, bsave:'.SC3', gs:'.SR4'},	// GRAPH SAURUS
	{ext:'.SR3', screen_no: 4, interlace:0, page:0, type:1, bsave:'.SC4', gs:'.SR3'},	// GRAPH SAURUS
	{ext:'.SR5', screen_no: 5, interlace:0, page:0, type:1, bsave:'.SC5', gs:'.SR5'},	// GRAPH SAURUS
	{ext:'.SR6', screen_no: 6, interlace:0, page:0, type:1, bsave:'.SC6', gs:'.SR6'},	// GRAPH SAURUS
	{ext:'.SR7', screen_no: 7, interlace:0, page:0, type:1, bsave:'.SC7', gs:'.SR7'},	// GRAPH SAURUS
	{ext:'.SR8', screen_no: 8, interlace:0, page:0, type:1, bsave:'.SC8', gs:'.SR8'},	// GRAPH SAURUS
	{ext:'.SRA', screen_no:10, interlace:0, page:0, type:0, bsave:'.S10', gs:'.SRA'},	// GRAPH SAURUS
	{ext:'.SRC', screen_no:12, interlace:0, page:0, type:0, bsave:'.S12', gs:'.SRC'},	// GRAPH SAURUS
	{ext:'.SRS', screen_no:12, interlace:0, page:0, type:1, bsave:'.S12', gs:'.SRS'},	// GRAPH SAURUS

    {ext:'.R50', screen_no: 5, interlace:1, page:0, type:1, bsave:'.S50', gs:'.R50'},	// GRAPH SAURUS interlace
    {ext:'.R51', screen_no: 5, interlace:1, page:1, type:1, bsave:'.S51', gs:'.R51'},	// GRAPH SAURUS interlace
	{ext:'.R60', screen_no: 6, interlace:1, page:0, type:1, bsave:'.S60', gs:'.R60'},	// GRAPH SAURUS interlace
    {ext:'.R61', screen_no: 6, interlace:1, page:1, type:1, bsave:'.S61', gs:'.R61'},	// GRAPH SAURUS interlace
	{ext:'.R70', screen_no: 7, interlace:1, page:0, type:1, bsave:'.S70', gs:'.R70'},	// GRAPH SAURUS interlace
    {ext:'.R71', screen_no: 7, interlace:1, page:1, type:1, bsave:'.S71', gs:'.R71'},	// GRAPH SAURUS interlace
	{ext:'.R80', screen_no: 8, interlace:1, page:0, type:1, bsave:'.S80', gs:'.R80'},	// GRAPH SAURUS interlace
    {ext:'.R81', screen_no: 8, interlace:1, page:1, type:1, bsave:'.S81', gs:'.R81'},	// GRAPH SAURUS interlace
	{ext:'.RA0', screen_no:10, interlace:1, page:0, type:1, bsave:'.SA0', gs:'.RA0'},	// GRAPH SAURUS interlace
    {ext:'.RA1', screen_no:10, interlace:1, page:1, type:1, bsave:'.SA1', gs:'.RA1'},	// GRAPH SAURUS interlace
	{ext:'.RC0', screen_no:12, interlace:1, page:0, type:1, bsave:'.SC0', gs:'.RC0'},	// GRAPH SAURUS interlace
    {ext:'.RC1', screen_no:12, interlace:1, page:1, type:1, bsave:'.SC1', gs:'.RC1'},	// GRAPH SAURUS interlace

    // 特殊 
    {ext:'.BIN', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.BIN', gs:'.BIN'},	// 汎用
    {ext:'.SPR', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.SPR', gs:'.SPR'},	// スプライト
    {ext:'.SPC', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.SPC', gs:'.SPC'},	// スプライトカラー
    {ext:'.NAM', screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.NAM', gs:'.NAM'},	// SC2 パターンネーム
    {ext:'.COL', screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.COL', gs:'.COL'},	// SC2 パターンカラー
    {ext:'.GEN', screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.GEN', gs:'.GEN'},	// SC2 パターンジェネレータ
    {ext:'.PAT', screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.PAT', gs:'.PAT'},	// SC2 パターンジェネレータ

    {ext:'.NM' , screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.NM' , gs:'.NM' },	// SC2 パターンネーム
    {ext:'.CL' , screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.CL' , gs:'.CL' },	// SC2 パターンカラー
    {ext:'.GN' , screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.GN' , gs:'.GN' },	// SC2 パターンジェネレータ

    {ext:'.CL0', screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.CL0', gs:'.CL0'},	// SC2 パターンカラー
    {ext:'.CL1', screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.CL1', gs:'.CL1'},	// SC2 パターンカラー
    {ext:'.CL2', screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.CL2', gs:'.CL2'},	// SC2 パターンカラー

    {ext:'.GN0', screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.GN0', gs:'.GN0'},	// SC2 パターンジェネレータ
    {ext:'.GN1', screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.GN1', gs:'.GN1'},	// SC2 パターンジェネレータ
    {ext:'.GN2', screen_no: 2, interlace:-1, page:-1, type:0, bsave:'.GN2', gs:'.GN2'},	// SC2 パターンジェネレータ

    // 対応未定：スクリーン0、1
    //	{ext:'.SC1', screen_no: 1, interlace:0, page:0, type:0, bsave:'.SC1', gs:'.SR1'},	// BSAVE
    {ext:'.TX1', screen_no: 0, txw:40, interlace:0, page:0, type:0, bsave:'.TX1', gs:'.TX1'},	// BSAVE / GS
    {ext:'.TX2', screen_no: 0, txw:80, interlace:0, page:0, type:0, bsave:'.TX2', gs:'.TX2'},	// BSAVE / GS
    {ext:'.GR1', screen_no: 1,         interlace:0, page:0, type:0, bsave:'.GR1', gs:'.GR1'},	// BSAVE / GS
    {ext:'.SR0', screen_no: 0, txw:40, interlace:0, page:0, type:0, bsave:'.SR0', gs:'.SR0'},	// BSAVE / GS
    {ext:'.SR1', screen_no: 1,         interlace:0, page:0, type:0, bsave:'.SR1', gs:'.SR1'},	// BSAVE / GS
];
function getExtInfo( ext )
{
	ext = ext.toUpperCase();
    if (ext.charAt(0) != '.') ext = '.' + ext;
	let idx = ext_info.findIndex(e => e.ext === ext);
	if (-1 < idx) return ext_info[idx];
	return null;
}
//================================================
// BSAVE/GSファイルヘッダー
//================================================
class BinHeader {
    static get HEADER_SIZE() { return 7; }
    static get HEAD_ID_LINEAR() { return 0xFE; } // BSAVE/GS LINEAR
    static get HEAD_ID_COMPRESS() { return 0xFD; } // #GS RLE COMPLESS

    constructor( d ) {
        this.id    = 0;
        this.start = 0;
        this.end   = 0;
        this.run   = 0;

        if (arguments.length > 0) {
            this.set( d );
        }
    }
    set( d ) {
        this.id    = d[0];
        this.start = d[1] + d[2] * 256;
        this.end   = d[3] + d[4] * 256;
        this.run   = d[5] + d[6] * 256;
    }
    get isBinary() {
        return (this.id == BinHeader.HEAD_ID_LINEAR);
    }
    get isCompress() {
        return (this.id == BinHeader.HEAD_ID_COMPRESS);
    }
    toBin() {
        return Uint8Array.from([
            this.id, 
            this.start & 255,
            (this.start >> 8) & 255,
            this.end & 255,
            (this.end >> 8) & 255,
            this.run & 255,
            (this.run >> 8) & 255,
        ]);
    }
    get size() {
        if (this.id == BinHeader.HEAD_ID_COMPRESS) {
            return this.end;
        } else {
            return this.end - this.start + 1;
        }
    }
}

//================================================
// クランプ
//================================================
function clamp( n, min, max ) {
    n = Math.max( min, Math.min( n, max ) );
    return n;
}


//================================================
// カラーパレット
//================================================
class Palette {
    [Symbol.toStringTag] = 'Palette';
    /*
        MSX palette 777
        16bit - 0grb
        8bit - rb, 0g
    */
    constructor( r, g, b ) {
        this.r = 0;
        this.g = 0;
        this.b = 0;
        if (arguments.length == 1) {
            if (toString.call( r ) == '[object Palette]') {
            	this.copy( r );
            } else {
	            this.w = r;
	        }
        } else
        if (arguments.length == 3) {
            this.setv(r, g, b);
        }
    }
    copy( s ) {
        this.r = s.r;
        this.g = s.g;
        this.b = s.b;
    }
    setv( r, g, b ) {
        this.r = r  & 7;
        this.g = g  & 7;
        this.b = b  & 7;
    }
    set w( w ) {
        this.r = (w >> 4) & 7;
        this.g = (w >> 8) & 7;
        this.b = (w >> 0) & 7;
    }
    get a() {
        return [ this.r * 16 + this.b, this.g ];
    }
    get rgb777() {
        return this.r * 16 + this.g * 256 + this.b;
    }
    get rgba() {
        return Uint8Array.from([
            Math.floor(255 * this.r / 7),
            Math.floor(255 * this.g / 7),
            Math.floor(255 * this.b / 7),
            0xff]);
    }
    get rgb_string() {
        var r = this.rgba;
        //return 'rgb('+r[0]+','+r[1]+','+r[2]+')';
        return `rgb( ${r[0]}, ${r[1]}, ${r[2]} )`;
    }
};

//================================================
// VDP
//================================================
class VDP {
    [Symbol.toStringTag] = 'VDP';
    /*
        MSX VDP
    */
    //------------------------------------------------
/*
    static get img_width () { return 564; }
	static get img_height() { return 480; }
	static get img_width () { return 640; }
	static get img_height() { return 480; }
*/
	static get aspect_ratio () { return 1.133; }  // konamiman (4/564.8522)/(3/480) = 1.133039756
	static get aspect_ratio2() { return 1.175; } // openMSX 3x:904 2x:603 1x:301

    static get screen_width () { return 512; }
	static get screen_height() { return 424; }

	static get vram_size() { return 0x20000; }	// 128 * 1024;

    static get palette_count() { return 16; }

    //------------------------------------------------
    // MSX2標準カラーパレット
    static get msx2pal() { return [
        0x0000,0x0000,0x0611,0x0733, 0x0117,0x0327,0x0151,0x0627,
        0x0171,0x0373,0x0661,0x0664, 0x0411,0x0265,0x0555,0x0777,
    ]; }
    // MSX1風カラーパレット
    static get msx1fpal() { return [
        0x0000,0x0000,0x0533,0x0644, 0x0237,0x0347,0x0352,0x0536,
        0x0362,0x0463,0x0653,0x0664, 0x0421,0x0355,0x0555,0x0777,
    ]; }

    //------------------------------------------------
    // 画面モード別 スペック
    static get screen_mode_spec1() { return [
        { no: 0, txw:40, txh:24, name:'TEXT1',      width:240, height:192, bpp:0, page_size:0x04000, }, 
        { no: 0, txw:80, txh:24, name:'TEXT2',      width:480, height:192, bpp:0, page_size:0x04000, }, 
        { no: 1, txw:32, txh:24, name:'GRAPHIC1',   width:256, height:192, bpp:0, page_size:0x04000, }, 
        { no: 2, txw:32, txh:24, name:'GRAPHIC2',   width:256, height:192, bpp:0, page_size:0x04000, }, 
        { no: 3, txw:32, txh:24, name:'MULTICOLOR', width:256, height:192, bpp:0, page_size:0x04000, }, 
        { no: 4, txw:32, txh:24, name:'GRAPHIC3',   width:256, height:192, bpp:0, page_size:0x04000, }, 
        { no: 5, txw:32, txh:26, name:'GRAPHIC4',   width:256, height:212, bpp:4, page_size:0x08000, }, 
        { no: 6, txw:64, txh:26, name:'GRAPHIC5',   width:512, height:212, bpp:2, page_size:0x08000, }, 
        { no: 7, txw:64, txh:26, name:'GRAPHIC6',   width:512, height:212, bpp:4, page_size:0x10000, }, 
        { no: 8, txw:32, txh:26, name:'GRAPHIC7',   width:256, height:212, bpp:8, page_size:0x10000, }, 
        { no: 9, txw:64, txh:26, name:'GRAPHIC8',   width:512, height:212, bpp:2, page_size:0x08000, }, 
        { no:10, txw:32, txh:26, name:'YAE',        width:256, height:212, bpp:8, page_size:0x10000, }, 
        { no:11, txw:32, txh:26, name:'YAE',        width:256, height:212, bpp:8, page_size:0x10000, }, 
        { no:12, txw:32, txh:26, name:'YJK',        width:256, height:212, bpp:8, page_size:0x10000, }, 
    ]; }
    // 画面モード別キャラジェネ設定
    static get screen_mode_spec2() { return [
        { no: 0, txw:40, namsiz:0x00400, patnam:0x0000, patgen:0x0800, patcol:-1    , paltbl:0x0400, s192:0x0FFF, s212:0x0FFF, }, 
        { no: 0, txw:80, namsiz:0x00800, patnam:0x0000, patgen:0x1000, patcol:0x0800, paltbl:0x0F00, s192:0x17FF, s212:0x17FF, }, 
        { no: 1, txw:32, namsiz:0x00200, patnam:0x1800, patgen:0x0000, patcol:0x2000, paltbl:0x2020, s192:0x37FF, s212:0x37FF, }, 
        { no: 2, txw:32, namsiz:0x00200, patnam:0x1800, patgen:0x0000, patcol:0x2000, paltbl:0x1B80, s192:0x37FF, s212:0x37FF, }, 
        { no: 3, txw:32, namsiz:0x00200, patnam:0x0800, patgen:0x0000, patcol:-1    , paltbl:0x2020, s192:0x37FF, s212:0x37FF, }, 
        { no: 4, txw:32, namsiz:0x00200, patnam:0x1800, patgen:0x0000, patcol:0x2000, paltbl:0x1B80, s192:0x37FF, s212:0x37FF, }, 
        { no: 5, txw:32, namsiz:0x08000, patnam:0x0000, patgen:-1    , patcol:-1    , paltbl:0x7680, s192:0x5FFF, s212:0x69FF, }, 
        { no: 6, txw:64, namsiz:0x08000, patnam:0x0000, patgen:-1    , patcol:-1    , paltbl:0x7680, s192:0x5FFF, s212:0x69FF, }, 
        { no: 7, txw:64, namsiz:0x10000, patnam:0x0000, patgen:-1    , patcol:-1    , paltbl:0xFA80, s192:0xBFFF, s212:0xD3FF, }, 
        { no: 8, txw:32, namsiz:0x10000, patnam:0x0000, patgen:-1    , patcol:-1    , paltbl:0xFA80, s192:0xBFFF, s212:0xD3FF, }, 
        { no: 9, txw:64, namsiz:0x08000, patnam:0x0000, patgen:-1    , patcol:-1    , paltbl:0x7680, s192:0x5FFF, s212:0x69FF, }, 
        { no:10, txw:32, namsiz:0x10000, patnam:0x0000, patgen:-1    , patcol:-1    , paltbl:0xFA80, s192:0xBFFF, s212:0xD3FF, }, 
        { no:11, txw:32, namsiz:0x10000, patnam:0x0000, patgen:-1    , patcol:-1    , paltbl:0xFA80, s192:0xBFFF, s212:0xD3FF, }, 
        { no:12, txw:32, namsiz:0x10000, patnam:0x0000, patgen:-1    , patcol:-1    , paltbl:0xFA80, s192:0xBFFF, s212:0xD3FF, }, 
    ]; }
    // 画面モード別スプライト設定
    static get screen_mode_spec3() { return [
    	//                                                               
        { no: 0, txw:40, spratr:-1    , sprgen:-1    , sprcol:-1    , }, 
        { no: 0, txw:80, spratr:-1    , sprgen:-1    , sprcol:-1    , }, 
        { no: 1, txw:32, spratr:0x1B00, sprgen:0x3800, sprcol:-1    , }, 
        { no: 2, txw:32, spratr:0x2000, sprgen:0x3800, sprcol:-1    , }, 
        { no: 3, txw:32, spratr:0x0800, sprgen:0x3800, sprcol:-1    , }, 
        { no: 4, txw:32, spratr:0x2000, sprgen:0x3800, sprcol:0x3800, }, 
        { no: 5, txw:32, spratr:0x7600, sprgen:0x7800, sprcol:0x7400, }, 
        { no: 6, txw:64, spratr:0x7600, sprgen:0x7800, sprcol:0x7400, }, 
        { no: 7, txw:64, spratr:0xFA00, sprgen:0xF000, sprcol:0xF800, }, 
        { no: 8, txw:32, spratr:0xFA00, sprgen:0xF000, sprcol:0xF800, }, 
        { no: 9, txw:64, spratr:0x7600, sprgen:0x7800, sprcol:0x7400, }, 
        { no:10, txw:32, spratr:0xFA00, sprgen:0xF000, sprcol:0xF800, }, 
        { no:11, txw:32, spratr:0xFA00, sprgen:0xF000, sprcol:0xF800, }, 
        { no:12, txw:32, spratr:0xFA00, sprgen:0xF000, sprcol:0xF800, }, 
    ]; }
    static getScreenModeSetting( no, width ) {
    	if (0 < no) {
            // SCREEN 1 以上
    		no += 1;
    	} else {
            // SCREEN 0
            // width 40 か 80 か
            if ((width !== undefined) && (width > 40)) {
                no += 1;
            }
        }

        if ((no < 0) || (VDP.screen_mode_spec1.length <= no))
        {
            return null;
        }

    	// 結合して返す
    	let info = { ...VDP.screen_mode_spec1[no], ...VDP.screen_mode_spec2[no], ...VDP.screen_mode_spec3[no] };

        // VRAMパレットエントリエンド
        info.palend = info.paltbl + 32 -1;

        info.sPal = Math.max(info.s212, info.palend);
        return info;
    }

    //------------------------
    // コンストラクタ
    //------------------------
	constructor( canvas, pal_canvas, page0_canvas, page1_canvas ) {
        const p = this;

        //------------------------
        // vram area
        p.vram = new Uint8Array( VDP.vram_size );

        //------------------------
        // page
        p.draw_page = 0;
        p.disp_page = -1;

        //------------------------
        // initial palette
        // make default palette
        p.pal = new Array( VDP.palette_count );
        p.pal_rgba = new Array( VDP.palette_count );
        p.setPalReg16();
        
        //------------------------
        // screen8 color : GGGRRRBB
        // make screen8 color array
        p.pal256 = new Array( 256 );
        p.pal256_rgba = new Array( 256 );
        for (var i = 0; i < p.pal256.length; ++i) {
            p.pal256[i] = new Palette(
                (i >> 2) & 7, i >> 5, (i << 1) & 7);
            p.pal256_rgba[i] = p.pal256[i].rgba;
        }

        //------------------------
        // canvas
        p.canvas    = null;
        p.offscreen = [null, null]; // disp, work
        p.imgData   = null;

        p.pal_canvas = null;
        p.page_canvas = null;

        if (arguments.length >= 1) {
            p.canvas = canvas;
        }
        if (arguments.length >= 2) {
            p.pal_canvas = pal_canvas;
        }
        if (arguments.length >= 4) {
            p.page_canvas = [ page0_canvas, page1_canvas ];
        }

        //------------------------
        // screen 情報
        p.screen_no = 5;
        p.mode_info = VDP.getScreenModeSetting( p.screen_no );
        p.width     = p.mode_info.width;
        p.height    = p.mode_info.height;
        p.force_height = 0;
        p.auto_detect_height = 0;
        p.img_width  = p.width;
        p.img_height = p.height;
        p.interlace_mode = 0;
        p.aspect_ratio = 1.177;
        p.changeScreen( p.screen_no , p.mode_info.txw, p.interlace_mode );
        p.cls();
    }

    //------------------------
    // カラーパレット設定
    //------------------------
    setPalReg16( paldat ) {
        const p = this;
        if (arguments.length < 1)
        {
            paldat = VDP.msx2pal;
        }
        for (var i = 0; i <VDP.palette_count; ++i) {
            p.pal[i] = new Palette( paldat[i] );
            p.pal_rgba[i] = p.pal[i].rgba;
        }
    }
    setPalReg8( d ) {
        const p = this;
        for (var i = 0; i < VDP.palette_count; ++i) {
            p.pal[i] = new Palette( d[i*2] + d[i*2+1] * 256 );
            p.pal_rgba[i] = p.pal[i].rgba;
        }
    }
    resetPalette() { this.setPalReg16(); }
    restorePalette( d ) {
        const p = this;
        if (arguments.length < 1) {
            p.setPalReg8( p.vram.subarray( p.mode_info.paltbl, p.mode_info.paltbl + 32  ) );
        } else {
            p.setPalReg8( d );
        }
    }

    getPalTbl() {
        const p = this;
        let d = new Uint8Array( VDP.palette_count * 2 );
        let idx = 0;
        for (var i = 0; i < VDP.palette_count; ++i, idx+=2) {
            d[idx + 0] = p.pal[i].rgb777 & 255;
            d[idx + 1] = (p.pal[i].rgb777 >> 8) & 255;
        }
        return d;
    }

    //------------------------
    // 画面モード変更
    //------------------------
    changeScreen( screen_no, txw, interlace_mode, force_height ) {
        const p = this;

        p.screen_no = screen_no;
        p.mode_info = VDP.getScreenModeSetting( screen_no, txw );
        p.width  = p.mode_info.width;
        p.height = p.mode_info.height;
        if (force_height === undefined) {
            force_height = p.force_height;
        }
        if (force_height) {
            p.height = force_height;
        }
        if (interlace_mode !== undefined ) {
            p.interlace_mode = interlace_mode;
        } else {
            p.interlace_mode = 0;
        }

        p.img_width  = p.width;
        p.img_height = p.height * (p.interlace_mode + 1);
        //console.log('img_height = ' + p.img_height);

        if (p.canvas) {
    		p.initCanvas();
        }
    }

    //------------------------
    // 描画キャンバス初期化
    //------------------------
    initCanvas( canvas, pal_canvas, page0_canvas, page1_canvas ) {
    	const p = this;

    	if (arguments.length >= 1) {
    		p.canvas = canvas;
    	}
        if (arguments.length >= 2) {
    		p.pal_canvas = pal_canvas;
        }
    	if (arguments.length >= 4) {
    		p.page_canvas = [ page0_canvas, page1_canvas ];
        }
        if (!p.canvas) {
            console.log('initCanvas - p.canvas is null.');
            return;
        }

         // イメージバッファ作成
         p.offscreen[0] = new OffscreenCanvas(p.img_width, p.img_height);
         p.offscreen[1] = new OffscreenCanvas(p.width, p.height * 2);
        var ctx = p.offscreen[1].getContext('2d');
        p.imgData = ctx.createImageData(p.offscreen[1].width, p.offscreen[1].height);
    }

    //------------------------
    // VRAMクリア
    //------------------------
    cls( resetPalette ) {
        const p = this;
        p.vram.fill( 0 );
        if (resetPalette === undefined) resetPalette = false;
        if (!pal_lock.checked || resetPalette) {
            p.resetPalette();
        }

        // 初期値
        const b = p.vram;
        const mode_info = p.mode_info;
        const tx_size = mode_info.txw * mode_info.txh;
        let n = mode_info.patnam;
        switch (p.screen_no) {
        case 0:
        case 1:
            b.fill(32,mode_info.patnam, mode_info.patnam + tx_size);
            b.fill(0xf0, mode_info.patcol, mode_info.patcol + 32);
            /*
            // test
            if (-1 < mode_info.patcol) {
                for (var i=0; i<32; ++i) {
                    b[mode_info.patcol + i] = i;
                }
            }
            for (let i = 0; i < tx_size; ++i, ++n) {
                b[n] = i;
            }
            */
            break;
        case 2:
        case 4:
            for (let i = 0; i < tx_size; ++i, ++n) {
                b[n] = i;
            }
            b.fill(0xf0, mode_info.patcol, mode_info.patcol + tx_size * 8);
            /*
            // test
            for (var i=0; i<tx_size * 8; ++i) {
                b[mode_info.patcol + i] = i;
            }
            */
            break;
        case 3:
            for (let i = 0; i < tx_size; ++i, ++n) {
                b[n] = (i & 31) + 32 * (i >> 2);
            }
            /*
            // test
            for (var i=0; i<tx_size * 8; ++i) {
                b[mode_info.patgen + i] = i;
            }
            */
            break;
        }
    }

    //------------------------
    // バイナリ転送
    //------------------------
    loadBinary( d, offset )
    {
    	const p = this;
        if (offset == undefined) {
            offset = p.draw_page * p.mode_info.namsiz;
        }
        let limit = p.vram.length - offset;
        if (offset > limit) {
            return;
        }
        if (d.length > limit) {
            p.vram.set( d.subarray(0, limit), offset );
        } else {
            p.vram.set( d, offset );
        }
    }

    setCanvasSize()
    {
    	const p = this;
        if (p.canvas) {
            // メインキャンバスサイズ
            p.canvas.height = p.height * 2;
            if (p.width <= 256) {
                p.canvas.width = p.width * 2 * p.aspect_ratio;
            } else {
                p.canvas.width = p.width * p.aspect_ratio;
            }
        }
    }

    //------------------------
    // 描画
    //------------------------
    draw( disp_mode ) {
    	const p = this;

        //------------------------
        // メインキャンバス
        //------------------------
        if (p.canvas) {
            p.setCanvasSize();

            var ctx = p.canvas.getContext('2d');
            ctx.imageSmoothingEnabled = false;//canvas_smoothing.checked;

            if (!p.interlace_mode) {
                ctx.drawImage( p.offscreen[0],
                    0, 0, p.canvas.width, p.canvas.height );
            } else {
                switch (p.disp_page) {
                case 0:
                case 1:
                    ctx.drawImage( p.offscreen[1], 
                        0, p.disp_page * p.height, p.width, p.height,
                        0, 0, p.canvas.width, p.canvas.height );
                    break;
                default:
                    ctx.drawImage( p.offscreen[0],
                        0, 0, p.img_width, p.img_height,
                        0, 0, p.canvas.width, p.canvas.height );
                    break;
                }
            }
        }

        //------------------------
        // ページ毎表示キャンバス
        //------------------------
        if (p.page_canvas) {
            let off_pg = 0;
            if (p.interlace_mode || (p.screen_no < 5)) ++off_pg;
            var offscreen = p.offscreen[off_pg];

            for (var pg = 0; pg < p.page_canvas.length; ++pg) {
                var canvas = p.page_canvas[pg];
                if (canvas) {
                    canvas.width  = p.canvas.width;
                    canvas.height = p.canvas.height;
                    ctx = canvas.getContext('2d');
                    ctx.imageSmoothingEnabled = false;//canvas_smoothing.checked;
                    ctx.drawImage( offscreen, 
                        0, pg * p.height, p.width, p.height,
                        0, 0, canvas.width, canvas.height );
                }
            }
        }

        //------------------------
        // パレットキャンバス
        //------------------------
        if (p.pal_canvas)
        {
            var pal = p.pal;
            if (p.screen_no == 8) {
                pal = p.pal256;
            }

            var canvas = p.pal_canvas;
            var ctx = canvas.getContext('2d');

            canvas.width = 32 * VDP.palette_count;
            canvas.height = 24;

            ctx.fillStyle = "black";
            ctx.fillRect(0,0,canvas.width,canvas.height);

            var w = Math.floor(canvas.width / pal.length);
            for (var i = 0; i < pal.length; ++i) {
                ctx.fillStyle = pal[i].rgb_string;
                ctx.fillRect(
                    canvas.width * i / pal.length, 0,
                    w, canvas.height);
            }
        }
    }
    update() {
    	const p = this;
        if (!p.imgData) {
            console.log('const - this.imgData is null.');
            return;
        }
        switch (p.screen_no) {
        case 0:
            p.update_chrgen(0xff, 6, -1);
            break;
        case 1:
            p.update_chrgen(0xff, 8, 6);
            break;
        case 2:
        case 4:
            p.update_chrgen(0x3ff, 8, 0);
            break;
        case 3:
            p.update_multi_color();
            break;
        case 5:
        case 7:
            p.update_bitmap16();
            break;
        case 6:
        case 9:
            p.update_bitmap4();
            break;
        case 8:
            p.update_bitmap256();
            break;
        case 10:
            p.update_bitmap_yae();
            break;
        case 11:
        case 12:
            p.update_bitmap_yjk();
            break;
        }

        if (!p.interlace_mode && (5 <= p.screen_no)) {
            var ctx = p.offscreen[0].getContext('2d');
            ctx.putImageData( p.imgData, 0, 0 );
        } else {
            let work = p.offscreen[1];
            var ctx = work.getContext('2d');
            ctx.putImageData( p.imgData, 0, 0 );

            ctx = p.offscreen[0].getContext('2d');
            if (5 <= p.screen_no) {
                let y = 0;
                for (var i = 0; i < p.height;  ++i, y+=2) {
                    ctx.drawImage( work, 0, i           , p.width, 1, 0, y    , p.width, 1 );
                    ctx.drawImage( work, 0, i + p.height, p.width, 1, 0, y + 1, p.width, 1 );
                }
            } else {
                ctx.putImageData( p.imgData, 0, 0 );
            }
        }
    }
    update_chrgen( chr_mask, chr_w, col_shift ) {
    	const p = this;

        if (!p.imgData) {
            console.log('update_chrgen - this.imgData is null.');
            return;
        }
        const pg_count = 2;//p.interlace_mode + 1;
        let buf = p.imgData.data;
        let d = p.vram;
        let cd = p.vram;

        const patgen = p.mode_info.patgen;
        let patcol = p.mode_info.patcol;
        let txw = p.mode_info.txw;
        let txh = p.mode_info.txh;
        const  line_size = 4 * vdp.width;
        let chr_size = 4 * chr_w;

        let ndx = p.mode_info.patnam;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let i = 0;
            for (let y = 0; y < txh; ++y) {
                let ody = odx;
                for (let x = 0; x < txw; ++x) {
                    // chr gen view : page 1
                    let chr_d = i;
                    if (pg == 0) {
                        // main view : page 0
                        chr_d = (d[ndx++] + (i & 0xff00));
                    }
                    chr_d &= chr_mask;  // screen 1 / 2,4
                    chr_d *= 8;
                    let dy = ody;
                    for(var py = 0; py < 8; ++py, ++chr_d) {
                        let patbit = d[patgen + chr_d];
                        let colset = 0xf0;
                        if (-1 < col_shift) {
                            colset = cd[patcol + (chr_d >> col_shift)];
                        }
                        let dx = dy; 
                        for(var px = 0; px < chr_w; ++px, dx+=4) {
                            let c_shift = (patbit >> 5) & 4; // 128 >> 5 = 4
                            let c = p.pal_rgba[ (colset >> c_shift) & 15 ];
                            buf[ dx + 0 ] = c[0];
                            buf[ dx + 1 ] = c[1];
                            buf[ dx + 2 ] = c[2];
                            buf[ dx + 3 ] = c[3];
                            patbit <<= 1;
                        }
                        dy += line_size;
                    }
                    ody += chr_size;
                    ++i;
                }
                odx += 8 * line_size;
            }

            // page 1 = chara preview
            txw = 32;
            if (vdp.screen_no < 2) {
                txh = 8;
            }
        }
    }
    update_multi_color() {
    	const p = this;

        if (!p.imgData) {
            console.log('update_multi_color - this.imgData is null.');
            return;
        }
        const pg_count = 2;//p.interlace_mode + 1;
        let buf = p.imgData.data;
        let d = p.vram;

        const patnam = p.mode_info.patnam;
        const patgen = p.mode_info.patgen;
        const txw = p.mode_info.txw;
        const txh = p.mode_info.txh;
        const tx_size = txw * txh;
        const line_size = 4 * vdp.width;
        const b_line_size = line_size * 4; // 1block 4x4px

        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            for (var y = 0; y < txh; ++y) {
                let dx = odx;
                for (var x = 0; x < txw; ++x) {
                    let chr;
                    if (pg) {
                        chr = x + (y >> 2) * txw;
                    } else {
                        chr = d[patnam + x + y * txw];
                    }
                    let dy = dx;
                    for (var iy = 0; iy < 2; ++iy) {
                        let colval = d[ patgen + (chr * 8) + (y & 3) * 2 + iy ];
                        // 8x4
                        let ddy = dy;
                        for (var diy = 0; diy < 4; ++diy) {
                            // 8x1
                            let ddx = ddy;
                            for(var c_shift = 4; c_shift >= 0; c_shift -= 4) {
                                var c = p.pal_rgba[ (colval >> c_shift) & 15 ];
                                // 4x1
                                for (var dix = 0; dix < 4; ++dix) {
                                    buf[ ddx++ ] = c[0];
                                    buf[ ddx++ ] = c[1];
                                    buf[ ddx++ ] = c[2];
                                    buf[ ddx++ ] = c[3];
                                }
                            }
                            ddy += line_size;
                        }
                        dy += b_line_size;
                    }
                    dx += 32; // 8 * 4;
                }
                odx += b_line_size + b_line_size;
            }
        }
    }
    update_bitmap16() {
    	const p = this;
        if (!p.imgData) {
            console.log('update_bitmap16 - this.imgData is null.');
            return;
        }
        const pg_count = 2;//p.interlace_mode + 1;
        const sz = p.width / 2 * p.height;
        let buf = p.imgData.data;
        let d = p.vram;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let idx = p.mode_info.patnam
                    + p.mode_info.namsiz * pg;
            for (var i = 0; i < sz; ++i) {
                let px = d[idx];
                let c = p.pal_rgba[px >> 4];
                buf[ odx + 0 ] = c[0];
                buf[ odx + 1 ] = c[1];
                buf[ odx + 2 ] = c[2];
                buf[ odx + 3 ] = c[3];
                c = p.pal_rgba[px & 15];
                buf[ odx + 4 ] = c[0];
                buf[ odx + 5 ] = c[1];
                buf[ odx + 6 ] = c[2];
                buf[ odx + 7 ] = c[3];
                odx += 8;
                idx += 1;
            }
        }
    }
    update_bitmap4() {
    	const p = this;
        if (!p.imgData) {
            console.log('update_bitmap16 - this.imgData is null.');
            return;
        }
        const pg_count = 2;//p.interlace_mode + 1;
        const sz = p.width / 4 * p.height;
        let buf = p.imgData.data;
        let d = p.vram;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let idx = p.mode_info.patnam
                    + p.mode_info.namsiz * pg;
            for (var i = 0; i < sz; ++i) {
                let px = d[idx];
                for (var c_shift = 6; c_shift>= 0; c_shift-=2 ) {
                    let c = p.pal_rgba[(px >> c_shift) & 3];
                    buf[ odx + 0 ] = c[0];
                    buf[ odx + 1 ] = c[1];
                    buf[ odx + 2 ] = c[2];
                    buf[ odx + 3 ] = c[3];
                    odx += 4;
                }
                idx += 1;
            }
        }
    }
    update_bitmap256() {
    	const p = this;
        if (!p.imgData) {
            console.log('update_bitmap256 - this.imgData is null.');
            return;
        }
        const pg_count = 2;//p.interlace_mode + 1;
        const sz = p.width * p.height;
        let buf = p.imgData.data;
        let d = p.vram;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let idx = p.mode_info.patnam
                    + p.mode_info.namsiz * pg;
            for (var i = 0; i < sz; ++i) {
                let px = d[idx];
                let c = p.pal256_rgba[px];
                buf[ odx + 0 ] = c[0];
                buf[ odx + 1 ] = c[1];
                buf[ odx + 2 ] = c[2];
                buf[ odx + 3 ] = c[3];
                odx += 4;
                idx += 1;
            }
        }
    }
    update_bitmap_yjk() {
    	const p = this;

        if (!p.imgData) {
            console.log('update_bitmap_yjk - this.imgData is null.');
            return;
        }
        let y = [0,0,0,0];  // 0 ~ 31
        let j = 0;  // -32 ~ +31
        let k = 0;  // -32 ~ +31

        const pg_count = 2;//p.interlace_mode + 1;
        const sz = p.width * p.height;
        let buf = p.imgData.data;
        let d = p.vram;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let idx = p.mode_info.patnam
                    + p.mode_info.namsiz * pg;
            for (var i = 0; i < sz; i+=4) {
                y[0] = d[idx] >> 3; k = d[idx] & 7;        ++idx;
                y[1] = d[idx] >> 3; k += (d[idx] & 7) * 8; ++idx;
                y[2] = d[idx] >> 3; j = d[idx] & 7;        ++idx;
                y[3] = d[idx] >> 3; j += (d[idx] & 7) * 8; ++idx;
                if (k > 31) k -= 64;
                if (j > 31) j -= 64;
                for (var h = 0; h < 4; ++h) {
                    buf[ odx + 0 ] = Math.floor( clamp(y[h] + j, 0, 31) * 255 / 31 );
                    buf[ odx + 1 ] = Math.floor( clamp(y[h] + k, 0, 31) * 255 / 31 );
                    buf[ odx + 2 ] =  Math.floor( 
                         clamp(y[h] * 5 / 4 - j / 2 - k / 4, 0, 31) * 255 / 31 );
                    buf[ odx + 3 ] = 255;
                    odx += 4;
                }
            }
        }
    }
    update_bitmap_yae() {
    	const p = this;

        if (!p.imgData) {
            console.log('update_bitmap_yae - this.imgData is null.');
            return;
        }
        let y = [0,0,0,0];  // 0 ~ 31 / bit0 == 1 -> index color
        let j = 0;  // -32 ~ +31
        let k = 0;  // -32 ~ +31

        const pg_count = 2;//p.interlace_mode + 1;
        const sz = p.width * p.height;
        let buf = p.imgData.data;
        let d = p.vram;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let idx = p.mode_info.patnam
                    + p.mode_info.namsiz * pg;
            for (var i = 0; i < sz; i+=4) {
                y[0] = d[idx] >> 3; k = d[idx] & 7;        ++idx;
                y[1] = d[idx] >> 3; k += (d[idx] & 7) * 8; ++idx;
                y[2] = d[idx] >> 3; j = d[idx] & 7;        ++idx;
                y[3] = d[idx] >> 3; j += (d[idx] & 7) * 8; ++idx;
                if (k > 31) k -= 64;
                if (j > 31) j -= 64;
                for (var h = 0; h < 4; ++h) {
                    if (y[h] & 1) {
                        let c = p.pal_rgba[ y[h] >> 1 ];
                        buf[ odx + 0 ] = c[0];
                        buf[ odx + 1 ] = c[1];
                        buf[ odx + 2 ] = c[2];
                        buf[ odx + 3 ] = c[3];
                    } else {
                        buf[ odx + 0 ] = Math.floor( clamp(y[h] + j, 0, 31) * 255 / 31 );
                        buf[ odx + 1 ] = Math.floor( clamp(y[h] + k, 0, 31) * 255 / 31 );
                        buf[ odx + 2 ] =  Math.floor( clamp(y[h]*5/4 - j/2 - k/4, 0, 31) * 255 / 31 );
                        buf[ odx + 3 ] = 255;
                    }
                    odx += 4;
                }
            }
        }
    }
};

let vdp = null;

// ========================================================
// 空白桁埋め数値文字列
// in:  n - 数値
//      d - 桁数
// ========================================================
function formatNum( n, d ) {
    if (n < 0) {
        return '-' + ('       ' + (-n)).slice(-d);
    }
    return ('   ' + n).slice(-d);
}

// ========================================================
// ゼロ桁埋め数値文字列
// in:  n - 数値
//      d - 桁数
// ========================================================
function formatNum0( n, d ) {
    if (n < 0) {
        return '-' + ('0000000' + (-n)).slice(-d);
    }
    return ('0000000' + n).slice(-d);
}

// ========================================================
// 空白桁埋め16進数文字列
// in:  n - 数値
//      d - 桁数
// ========================================================
function formatHex( n, d ) {
    if (n < 0) {
        return '-' + ('       ' + (-n).toString(16).toUpperCase()).slice(-d);
    }
    return ('       ' + n.toString(16).toUpperCase()).slice(-d);
}

// ========================================================
// ゼロ桁埋め16進数文字列
// in:  n - 数値
//      d - 桁数
// ========================================================
function formatHex0( n, d ) {
    if (n < 0) {
        return '-' + ('0000000' + (-n).toString(16).toUpperCase()).slice(-d);
    }
    return ('0000000' + n.toString(16).toUpperCase()).slice(-d);
}

// ========================================================
// バイナリをダウンロードさせる
// ========================================================
function startDownload( dat, filename )
{
    const blob = new Blob( [dat], { "type" : "application/octet-stream" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement( 'a' );
    a.download = filename;
    a.href = url;
    a.click();
    a.remove();
    setTimeout(() => {
        URL.revokeObjectURL(url);
    }, 1E4);
}

// ========================================================
// ラジオスイッチ：チェックされた値を返す
//  in: name - タグのid
// ========================================================
function getCheckedRadioSwtchValue( name )
{
    let radio_sw = document.getElementsByName( name );
    for (let i = 0; i < radio_sw.length; ++i)
    {
        if (radio_sw[i].checked) {
            return radio_sw[i].value;
        }
    }
    return '';
}

// ========================================================
// MSX ANK 文字 -> Unicode/S-JIS系変換
// in:  d - Uint8Array
// ========================================================
function fromMSX_ankChar(d)
{
    const char_table = Array.from(
        '　月火水木金土日年円時分秒百千万'
        + 'π┴┬┤├┼│─┌┐└┘×大中小'
        + ' !"#$%&\'()*+,-./0123456789:;<=>?'
        + '@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_'
        + '`abcdefghijklmnopqrstuvwxyz{|}~ '
        + '♠❤♣♦〇●をぁぃぅぇぉゃゅょっ'
        + '　あいうえおかきくけこさしすせそ'
        ///*
        + ' ｡｢｣､･ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿ'
        + 'ﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ'
        //*/
        /*
        + '　。「」、・ヲァィゥェォャュョッ'
        + 'ーアイウエオカキクケコサシスセソ'
        + 'タチツテトナニヌネノハヒフヘホマ'
        + 'ミムメモヤユヨラリルレロワン゛゜'
        */
        + 'たちつてとなにぬねのはひふへほま'
        + 'みむめもやゆよらりるれろわん　■'
    );
    let graph = false;
    let res = '';
    for (i = 0; i < d.length; ++i) {
        let c = d[i];
        if (graph) {
            if ((64 <= c) && (c <= 95)) {
                res = res + char_table[c - 64];
            } else {
                res = res + ' ';
            }
            graph = false;
        } else
        if (c == 1) {
            graph = true;
        } else
        if ((32 <= c) && (c <= 255))
        {
            res = res + char_table[c];
        } else {
            res = res + ' ';
        }
    }
    return res;
}
// ========================================================
// GRAPH SAURUS RLE 展開
// ========================================================
function gs_rle_decode( dat, vram_size )
{
    if (vram_size === undefined) {
        vram_size = VDP.vram_size;
    }
    let buf = new Uint8Array( vram_size );

    let i = 0;
    let o = 0;

    while ( (o < vram_size) && (i < dat.length))
    {
        let b = dat[i++];
        if (0 == b) {
            let l = dat[i++];
            let v = dat[i++];
            for (; (o < vram_size) && (0 < l); --l) {
                buf[o++] = v;
            }
        } else
        if (b < 16) {
            let v = dat[i++];
            for (; (o < vram_size) && (0 < b); --b) {
                buf[o++] = v;
            }
        } else {
            buf[o++] = b;
        }
    }
    return buf.slice(0, o);
}

// ========================================================
// GRAPH SAURUS RLE 圧縮
// ========================================================
function gs_rle_encode( dat, max_size )
{
    // l = count
    // v = value
    // buff = output buffer
    // o = output buffer pointer
    function flash( l, v, buff, o)
    {
        // 値が変化したので書き出し
        if ((1 == l) && (16 <= v)) {
            // 長さ1で値が16以上なら直接値
            buf[o++] = v;
        } else
        if (l < 16 ) {
            // 長さが16未満なら長さ+値
            if (buff.length <= (o + 2)) {
                return -1;
            }
            buf[o++] = l;
            buf[o++] = v;
        } else {
            // それ以外なら0+長さ+値
            if (buf.length <= (o + 3)) {
                return -1;
            }
            buf[o++] = 0;
            buf[o++] = l;
            buf[o++] = v;
        }
        return o;
    }

    if (max_size === undefined) {
        max_size = VDP.vram_size;
    }
    let buf = new Uint8Array( max_size );

    let i = 0;
    let o = 0;

    let searching = false;
    let b = 0;
    let v = 0;
    let l = 0;

    let need_push = false;

    while ((o < buf.length) && (i < dat.length))
    {
        b = dat[i++];
        if (searching) {
            if ((v != b) || (l == 255)) {
                o = flash( l, v, buf, o );
                searching = false;
            }
        } 
        if (!searching) {
            // 検索開始
            searching = true;
            v = b;
            l = 1;
        } else {
            l += 1;
        }
    }
    if (searching) {
        o = flash( l, v, buf, o );
    } 
    return buf.slice(0, o);
}

// ========================================================
// 画像保存バイナリ作成
// ========================================================
function createBsaveImage( start, size, page, isCompress )
{
    let dat = new Uint8Array( size + BinHeader.HEADER_SIZE );

    let header = new BinHeader();
    if (isCompress === undefined) isCompress = 0;
    if ( !isCompress ) {
        header.id = BinHeader.HEAD_ID_LINEAR;
        header.start = start;
        header.end = start + size - 1;
        header.run = 0;
    } else {
        header.id = BinHeader.HEAD_ID_COMPRESS;
        header.start = start;
        header.end = size;
        header.run = 0;
    }

    const offset = page * vdp.mode_info.page_size;
    let body = vdp.vram.subarray( start + offset, start + offset + size );
    if (header.id == BinHeader.HEAD_ID_COMPRESS) {
        let cbody = gs_rle_encode( body );
        body = cbody;
        header.end = cbody.length;
    }

    let header_bin = header.toBin();
    dat.set( header_bin, 0 );
    dat.set( body, header_bin.length );
    
    return dat.subarray(0, body.length + header_bin.length );
}

// ========================================================
// カラーパレット保存
// ========================================================
function savePalette()
{
    if (vdp.screen_no == 8) {
        // SCREEN8はパレットなし
        // スプライトパレットも固定
        return;
    }

    let f = null;
    if (pal_file.size) {
        f = pal_file;
    } else 
    if (main_file.size) {
        f = main_file;
    } else 
    if (sub_file.size) {
        f = sub_file;
    }
    if (f && f.name.length) {
        const fname = getBasename( f.name ) + ".PL" + vdp.screen_no.toString(16);
        pald = vdp.getPalTbl();
        add_log( '"' + fname + '": カラーパレット出力' );
        startDownload( pald, fname );
    }

}

// ========================================================
// 画像保存
// ========================================================
function saveImage(file, page, commpress, with_pal)
{
    f = file;
    if (f.size) {
        const ext_info = getExtInfo( getExt( f.name ) );
        if (!ext_info) return;

        let sav_ext;
        if (commpress) {
            sav_ext = ext_info.gs;
        } else {
            sav_ext = ext_info.bsave;
        }
        let fname = getBasename( f.name ) + sav_ext;

        let start = 0;
        let size = vdp.mode_info.page_size;
        // SCREEN 0～4はVRAM 0x0000～0x3FFFまるごとセーブ
        if (vdp.mode_info.bpp) {
            size = vdp.height * vdp.mode_info.bpp * vdp.width / 8;
        }
        if (with_pal) {
            let withpal_size = vdp.mode_info.palend + 1;
            if (size < withpal_size) {
                size = withpal_size;
            }
            if (withpal_size <= size) {
                vdp.vram.set( vdp.getPalTbl(), vdp.mode_info.paltbl );
            }
        }

        let out = createBsaveImage( start, size, page, commpress);
        if (commpress) {
            add_log( '"' + fname + '": GS圧縮出力' );
        } else {
            add_log( '"' + fname + '": BSAVE出力' );
        }
        startDownload( out, fname );
    }
}

// ========================================================
// 画像 縦サイズ 自動判定
// ========================================================
function detectImageHeight( mode_info, header, size )
{
    let force_height = 0;
    let end = header.start + size - 1;
    if ((0 == force_height) && (5 <= mode_info.no))
    {
        // 自動なら画像ピクセルサイズから表示サイズを判断
        if (header.isCompress && (mode_info.s212 < end)) {
            // 圧縮形式はパレットを含まないのでline212と比較
            force_height = 256;
        } else
        if (mode_info.palend < end) {
            // リニア形式はパレットテーブルを越えているかで判断
            force_height = 256;
        } else {
            force_height = mode_info.height;
        }
    }
    else
    {
        force_height = 192;
    }
    return force_height;
}

// ========================================================
// 画像バイナリ読み込み
// in:  d - Uint8Array
//      config - loadVcdConfig（設定オブジェクト）
// ========================================================
function loadImage(d, ext_info)
{
    // ========================================================
    // バイナリ解析開始
    // ========================================================
    let header = new BinHeader( d );
    let dat = d.subarray( BinHeader.HEADER_SIZE );
    if (header.isCompress)
    {
        // 圧縮の場合 end = 展開後のピクセルサイズ
        // dat = gs_rle_decode( dat, header.end );
        // 例外もありうるので一旦無視して上限をVRAMサイズ
        // 実際に展開したサイズまでのデータを返す
        dat = gs_rle_decode( dat );
    }

    let info = {
        screen_no:  ext_info.screen_no,
        interlace:  ext_info.interlace,
        page:       ext_info.page,
        txw:        ext_info.txw,
    };
    if (info.screen_no < 0) {
        info.screen_no = vdp.screen_no;
        info.interlace = vdp.interlace_mode;
        info.page = 0;
    }
    if (info.page < 0) info.page = 0;
    if (info.interlace < 0) {
        if (info.screen_no != vdp.screen_no) {
            info.interlace = 0;
        } else {
            info.interlace = vdp.interlace_mode;
        }
    }

    let mode_info = VDP.getScreenModeSetting( info.screen_no, info.txw );
    vdp.auto_detect_height = detectImageHeight( mode_info, header, dat.length );
    let disp_height = vdp.force_height;
    if (!disp_height) {
        disp_height = vdp.auto_detect_height;
    }

    if ((ext_info.page != 0) &&
         (ext_info.interlace != 0) &&
         (info.screen_no == vdp.screen_no) &&
         (info.interlace == vdp.interlace_mode) &&
         (disp_height == vdp.height)
       ) {
    } else {
        vdp.changeScreen( info.screen_no, info.txw, info.interlace, disp_height );
        vdp.cls( true );
    }
    if (!ext_info || !ext_info.page) {
        vdp.cls();
    }

    vdp.loadBinary(dat, 
        header.start + info.page * vdp.mode_info.page_size);

    // VRAMパレットテーブル読み込み
    if (4 <= vdp.screen_no) { // スクリーン4以上の場合のみ
        if (header.isBinary && !header.isCompress) {
            if (!ext_info.page && (header.end >= vdp.mode_info.palend)) {
                if (!pal_lock.checked) {
                    vdp.restorePalette(); 
                }
            }
        }
    }
    vdp.update();
    vdp.draw();

    return header;
}

// ========================================================
// 画像ファイルを開く
// ========================================================
function openGsFile( target_file )
{
    if (target_file == undefined) {
        return false;
    }

    // ファイル名表示
    let file_text = fileText(target_file);
    //add_log( 'read: ' + file_text );

    // 拡張子検査
    let file_ext = getExt(target_file.name);
    let is_pal = isPaletteFile(file_ext);
    let ext_info = getExtInfo(file_ext);
    if (!ext_info && !is_pal)
    {
        // 画像ファイルでなければ無視
        add_log( '"' + file_text + '": 画像ファイルではありません。' );
        return false;
    }

    // カレントファイル表示処理
    if (is_pal) {
        // パレット
        pal_file = LogFile( target_file );
    } else
    if ((ext_info.interlace < 0) || (ext_info.interlace < 0)) {
        // 現在とフォーマットが違う場合はクリア
        if (((ext_info.screen_no >= 0) && (vdp.screen_no != ext_info.screen_no)) ||
            ((ext_info.interlace >= 0) && (vdp.interlace_mode != ext_info.interlace)))
        {
            pal_file = empty_file;
            sub_file = empty_file;
            main_file = empty_file;
            vdp.cls();
        }
    } else
    if (ext_info.interlace && ext_info.page) {
        // メイン画像とフォーマットが違う場合はクリア
        if ((vdp.screen_no != ext_info.screen_no) ||
            (vdp.interlace_mode != ext_info.interlace))
        {
            pal_file = empty_file;
            main_file = empty_file;
            vdp.cls();
        }
        // 追加画像
        sub_file = LogFile( target_file );
    } else {
        // メイン画像
        pal_file = empty_file;
        sub_file = empty_file;
        main_file = LogFile( target_file );
        vdp.cls();
    }
    
    // ドロップ可能フラグを一時停止
    drop_avilable = false;
    //add_log( '"' + file_text + '": 読み込み中' );

    let config = {};

    // ========================================================
    // ファイル読み込み
    let reader = new FileReader();
    reader.onload = function(f) {
        let u8array = null;
        try {
            u8array = new Uint8Array(f.target.result);
        } catch (e) {
            add_log( '"' + file_text + '": 読み込みデータに問題があります' );
        }
        if (u8array != null)
        {
            if (is_pal) {
                vdp.restorePalette( u8array );
                vdp.update();
                vdp.draw();
            } else {
                let h = loadImage(u8array, ext_info);
                if (ext_info.interlace && ext_info.page) {
                    sub_file.header = h;
                } else {
                    main_file.header = h;
                }
                
            }
            add_log( '"' + file_text + '": 読み込み完了' );
        }
        drop_avilable = true;
        displayCurrentFilename();

        // 読み込み待ちキュー
        if (file_load_que.length)
        {
            openGsFile( file_load_que.shift() );
        }
        else
        {
            // 全て完了した後
            // 自動保存があれば実行
            saveAll();
        }
    };
    reader.onerror = function(e) {
        let errmes = new Array(
            "",
            "ファイルが見つかりません",
            "セキュリティエラーが検出されました",
            "ファイルの読込が中断されました",
            "ファイルの読み込み権限がありません",
            "ファイルサイズが大き過ぎます"
            );
            add_log( '"' + file_text + '": 読み込みエラーです \n\n'
                                + errmes[reader.error.code]  );
        drop_avilable = true;
        displayCurrentFilename();

        // 読み込み待ちキュー
        /*
        if (file_load_que.length)
        {
            openGsFile( file_load_que.shift(); )
        }
        */
        file_load_que.length = 0;    //残りをすべて破棄
    };

    drop_avilable = false;
    reader.readAsArrayBuffer(target_file);

    return true;
}


// ========================================================
//  複数ファイル読み込み
// ========================================================
function openFiles( files )
{
    let main = null;
    let sub = null;
    let pal = null;

    for (var i = 0; i < files.length; ++i) {

        let file_ext = getExt(files[i].name);
        let is_pal = isPaletteFile(file_ext);
        let ext_info = getExtInfo(file_ext);

        if (is_pal) {
            pal = files[i];
        } else
        if (ext_info) {
            if (ext_info.interlace && ext_info.page) {
                sub = files[i];
            } else {
                main = files[i];
            }
        } else {
            add_log( '"' + files[i].name + '": 読み込み対象ファイルではありません' );
        }

    }

    // 手抜き：
    // 待機チェーンで連続ロードする
    let result = true;
    if (main != null)  file_load_que.push( main );
    if (sub  != null)  file_load_que.push( sub  );
    if (pal  != null)  file_load_que.push( pal  );

    if (file_load_que.length) {
        openGsFile( file_load_que.shift() );
    }
    return true;
}

// ========================================================
// 全て保存
// ========================================================
function saveAll()
{
    let commpress = 0;
    let with_pal = 0;
    switch (quick_save_mode)
    {
        case quick_save_mode_value[1]:
            commpress = 0;
            with_pal  = 1;
            break;
        case quick_save_mode_value[2]:
            commpress = 0;
            with_pal  = 0;
            break;
        case quick_save_mode_value[3]:
            commpress = 1;
            with_pal  = 0;
            break;
        default:
            return;
    }
    let f = null;
    if (main_file.size && main_file.name.length) {
        saveImage( main_file, 0, commpress, with_pal );
    }
    if (sub_file.size && sub_file.name.length) {
        saveImage( sub_file, 1, commpress, with_pal );
    }
    if (!with_pal) {
        savePalette();
    }
}

// ========================================================
// ドラッグされたアイテムがファイルかどうか検査する関数
// in:  e - dropイベントオブジェクト
// ========================================================
function isValidDropItem(e)
{
    return (e.dataTransfer.types.indexOf("Files") >= 0)
        //&& (e.dataTransfer.items.length <= 1)
        ;
}

// ========================================================
// イベント：HTMLの読み込みが完了した
// ========================================================
window.addEventListener('DOMContentLoaded',
function() {
    vdp = new VDP();
    //console.log(vdp);

    // 各種画面要素
    const canvas_area = document.getElementById('canvas_area');
    const canvas_page0 = document.getElementById('canvas_page0');
    const canvas_page1 = document.getElementById('canvas_page1');
    const palette_area = document.getElementById('palette_area');

    //const drop_area = document.getElementById('drop_area');
    //const drop_area = canvas_area;
    const drop_area = document.body;

    // 読み込みファイル一覧（１）
    const filename_area = document.getElementById('filename_area');
    const filename_area2 = document.getElementById('filename_area2');
    const filename_area3 = document.getElementById('filename_area3');

    // ログメッセージ
    const log_text = this.document.getElementById('log_text');

    // ファイル情報詳細
    const spec_details = document.getElementById('spec_details');

    const detail_pal_file    = document.getElementById('detail_pal_file');
    const detail_page0_file = document.getElementById('detail_page0_file');
    const detail_page1_file = document.getElementById('detail_page1_file');

    const detail_page0_spec = document.getElementById('detail_page0_spec');
    const detail_page1_spec = document.getElementById('detail_page1_spec');

    // ボタン
    const pal_save            = document.getElementById('pal_save');
    const page0_save_bsave    = document.getElementById('page0_save_bsave');
    const page0_save_bsave_np = document.getElementById('page0_save_bsave_np');
    const page0_save_gsrle    = document.getElementById('page0_save_gsrle');
    const page1_save_bsave    = document.getElementById('page1_save_bsave');
    const page1_save_bsave_np = document.getElementById('page1_save_bsave_np');
    const page1_save_gsrle    = document.getElementById('page1_save_gsrle');

    // 情報表示
    const help_guide = document.getElementById('help_guide');

    // アコーディオンタブ
    const tab_title = document.getElementById('tab_title'); // help detail tag
    const tab_helps = document.getElementById('tab_helps'); // help detail tag
    const tab_settings = document.getElementById('tab_settings'); // settings detail tag

    // カラーパレット固定
    const pal_lock = document.getElementById('pal_lock');

    // キャンバススムージング
    //const canvas_smoothing = document.getElementById('canvas_smoothing');

    vdp.initCanvas( canvas_area, palette_area, canvas_page0, canvas_page1 );

    //log_text.innerText = '';
    help_guide.innerText = default_log_msg;
    
    displayCurrentFilename();

    // ========================================================
    // イベント：画面縦横比(DotAspect比)変更
    // ========================================================
    canvas_area.height = VDP.screen_height;
    const stretch_screen_radio = document.getElementsByName('stretch_screen');
    stretch_screen_radio.forEach(e => { 
        if (e.checked) {
            vdp.aspect_ratio = Number.parseFloat(e.value);
            vdp.draw();
        }
    });
    let onChangeStrechMode = function(event) {
        const e = event.srcElement;
        if (e.checked) {
            vdp.aspect_ratio = Number.parseFloat(e.value);
            vdp.draw();
        }
    }
    stretch_screen_radio.forEach(e => {
        e.addEventListener("change", onChangeStrechMode );
    });

    // ========================================================
    // イベント：画面縦サイズモード変更
    // ========================================================
    const height_mode_radio = document.getElementsByName('height_mode');
    let onChangeHeightMode = function(event) {
        const e = event.srcElement;
        if (e.checked) {
            vdp.force_height = Number.parseInt(e.value);

            let disp_height = vdp.force_height;
            if (!disp_height) {
                disp_height = vdp.auto_detect_height;
            }
            vdp.changeScreen( vdp.screen_no, vdp.mode_info.txw, vdp.interlace_mode, disp_height );
            vdp.update();
            vdp.draw();
        }
    }
    height_mode_radio.forEach(e => {
        e.addEventListener("change", onChangeHeightMode );
    });

    // ========================================================
    // イベント：ドラッグ中のアイテムがドラッグ領域
    // ========================================================
    drop_area.addEventListener('dragover',
    function(e) {
        e.preventDefault(); // ブラウザで開かないようにする
        e.stopPropagation();  // イベントを伝播させない

        if (!drop_avilable || !isValidDropItem(e))
        {
            // ファイルアイテムでなければ無視
            e.dataTransfer.dropEffect = 'none'; // ドラッグしているファイルアイコンを変更
            canvas_area.classList.remove('dropEffect');   // ドラッグ受付中スタイルシート解除
            return;
        }

        e.dataTransfer.dropEffect = 'copy'; // ドラッグしているファイルアイコンを変更
        canvas_area.classList.add('dropEffect');   // ドラッグ受付中スタイルシート設定
    });

    // ========================================================
    // イベント：ドラッグ領域の外に出た
    // ========================================================
    drop_area.addEventListener('dragleave',
    function(e) {
        //e.preventDefault(); // ブラウザで開かないようにする
        e.stopPropagation();  // イベントを伝播させない

        canvas_area.classList.remove('dropEffect');   // ドラッグ受付中スタイルシート解除
    });

    // ========================================================
    // イベント：ドロップされた
    // ========================================================
    drop_area.addEventListener("drop",
    function(e) {
        e.preventDefault(); // ブラウザで開かないようにする
        e.stopPropagation();  // イベントを伝播させない

        canvas_area.classList.remove('dropEffect');   // ドラッグ受付中スタイルシート解除

        if (!drop_avilable || !isValidDropItem(e))
        {
            // ファイルアイテムでなければ無視
            e.dataTransfer.dropEffect = "none"; // ドラッグしているファイルアイコンを変更
            return false;
        }

        // ファイルオープン
        if (!openFiles(e.dataTransfer.files)) {
            // error
        }
        e.dataTransfer.dropEffect = "none"; // ドラッグしているファイルアイコンを変更

        if (isFirst) {
            isFirst = false;
            //tab_title.removeAttribute('open');
            tab_helps.removeAttribute('open');
            //tab_settings.removeAttribute('open');
        }
    });

    // ========================================================
    // イベント：ファイルを開くボタン
    // ========================================================
    const file_open_button = document.getElementById("file_open");
    file_open_button.addEventListener("change",
    function() {
        if (file_open_button.files.length <= 0)
        {
            return;
        }

        // ファイルオープン
        // ファイルオープン
        if (!openFiles(file_open_button.files)) {
            // error
        }

        if (isFirst) {
            isFirst = false;
            //tab_title.removeAttribute('open');
            tab_helps.removeAttribute('open');
            //tab_settings.removeAttribute('open');
        }
    });

    // ========================================================
    // イベント：ファイルを開くラベルボタン
    // スペースキーかエンターでファイルを開く
    // ========================================================
    const file_open_label = this.document.getElementById("file_open_label");
    file_open_label.addEventListener("keyup",
    function(e) {
        switch (e.key) {
        case " ":
        case "Enter":
        {
            file_open_button.click();
            break;
        }
        }
    });

    // ========================================================
    // イベント：ファイルを保存するボタン
    // ========================================================
    // パレットファイル
    pal_save.addEventListener("click", 
    function(e) {
        savePalette();
    });
    // ========================================================
    // page 0 bsave
    page0_save_bsave.addEventListener("click",
    function(e) { saveImage( main_file, 0, 0, 1 ); });
    page0_save_bsave_np.addEventListener("click",
    function(e) { saveImage( main_file, 0, 0, 0 ); });
    page0_save_gsrle.addEventListener("click",
    function(e) { saveImage( main_file, 0, 1, 0 ); });
    // ========================================================
    // page 1 bsave
    page1_save_bsave.addEventListener("click",
    function(e) { saveImage( sub_file, 1, 0, 1 ); });
    page1_save_bsave_np.addEventListener("click",
    function(e) { saveImage( sub_file, 1, 0, 0 ); });
    page1_save_gsrle.addEventListener("click",
    function(e) { saveImage( sub_file, 1, 1, 0 ); });

    // ========================================================
    // イベント：自動保存モード変更
    // ========================================================
    const quick_save = document.getElementsByName('qick_save');
    let onChangeQuickSaveMode = function(event) {
        const e = event.srcElement;
        if (e.checked) {
            quick_save_mode = e.value;
        }
    }
    quick_save.forEach(e => {
        e.addEventListener("change", onChangeQuickSaveMode );
    });

    // ========================================================
    // キャンバススムージング
    // ========================================================
    //canvas_smoothing.addEventListener("change", function(e) { vdp.draw(); });
    // ぼやけすぎて使えない

    /* test
    vdp.changeScreen(1);
    vdp.cls();
    vdp.update();
    vdp.draw();
    */
});

