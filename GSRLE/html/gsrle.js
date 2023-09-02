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

let isFirst = true;

// ========================================================
// ドラッグアンドドロップ受付状態
// ========================================================
let drop_avilable = true;

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
        detail_page0_file.textContent = ':　' + fileText(main_file);
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
        detail_page1_file.textContent = ':　' + fileText(sub_file);
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
            detail_page1_spec.textContent = ':　[CHARACTER PATTERN GENERATOR TABLE]';
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
        detail_pal_file.textContent = ':　' + fileText(pal_file);
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
//	{ext:".SC1", screen_no: 1, interlace:0, page:0, type:0, bsave:".SC1", gs:".SR1"},	// BSAVE
	{ext:".SC2", screen_no: 2, interlace:0, page:0, type:0, bsave:".SC2", gs:".SR2"},	// BSAVE
	{ext:".SC3", screen_no: 3, interlace:0, page:0, type:0, bsave:".SC3", gs:".SR4"},	// BSAVE
	{ext:".SC4", screen_no: 4, interlace:0, page:0, type:0, bsave:".SC4", gs:".SR3"},	// BSAVE
	{ext:".SC5", screen_no: 5, interlace:0, page:0, type:0, bsave:".SC5", gs:".SR5"},	// BSAVE
	{ext:".SC6", screen_no: 6, interlace:0, page:0, type:0, bsave:".SC6", gs:".SR6"},	// BSAVE
	{ext:".SC7", screen_no: 7, interlace:0, page:0, type:0, bsave:".SC7", gs:".SR7"},	// BSAVE
	{ext:".SC8", screen_no: 8, interlace:0, page:0, type:0, bsave:".SC8", gs:".SR8"},	// BSAVE
	{ext:".S10", screen_no:10, interlace:0, page:0, type:0, bsave:".S10", gs:".SRA"},	// BSAVE
	{ext:".S12", screen_no:12, interlace:0, page:0, type:0, bsave:".S12", gs:".SRC"},	// BSAVE
	{ext:".SCA", screen_no:10, interlace:0, page:0, type:0, bsave:".SCA", gs:".SRA"},	// BSAVE
	{ext:".SCC", screen_no:12, interlace:0, page:0, type:0, bsave:".SCC", gs:".SRC"},	// BSAVE
	{ext:".S50", screen_no: 5, interlace:1, page:0, type:0, bsave:".S50", gs:".R50"},	// BSAVE interlace
    {ext:".S51", screen_no: 5, interlace:1, page:1, type:0, bsave:".S51", gs:".R51"},	// BSAVE interlace
	{ext:".S60", screen_no: 6, interlace:1, page:0, type:0, bsave:".S60", gs:".R60"},	// BSAVE interlace
    {ext:".S61", screen_no: 6, interlace:1, page:1, type:0, bsave:".S61", gs:".R61"},	// BSAVE interlace
	{ext:".S70", screen_no: 7, interlace:1, page:0, type:0, bsave:".S70", gs:".R70"},	// BSAVE interlace
    {ext:".S71", screen_no: 7, interlace:1, page:1, type:0, bsave:".S71", gs:".R71"},	// BSAVE interlace
	{ext:".S80", screen_no: 8, interlace:1, page:0, type:0, bsave:".S80", gs:".R80"},	// BSAVE interlace
    {ext:".S81", screen_no: 8, interlace:1, page:1, type:0, bsave:".S81", gs:".R81"},	// BSAVE interlace
	{ext:".SA0", screen_no:10, interlace:1, page:0, type:0, bsave:".SA0", gs:".RA0"},	// BSAVE interlace
    {ext:".SA1", screen_no:10, interlace:1, page:1, type:0, bsave:".SA1", gs:".RA1"},	// BSAVE interlace
	{ext:".SC0", screen_no:12, interlace:1, page:0, type:0, bsave:".SC0", gs:".RC0"},	// BSAVE interlace
    {ext:".SC1", screen_no:12, interlace:1, page:1, type:0, bsave:".SC1", gs:".RC1"},	// BSAVE interlace
	{ext:".SR2", screen_no: 2, interlace:0, page:0, type:1, bsave:".SC2", gs:".SR2"},	// GRAPH SAURUS
	{ext:".SR4", screen_no: 3, interlace:0, page:0, type:1, bsave:".SC3", gs:".SR4"},	// GRAPH SAURUS
	{ext:".SR3", screen_no: 4, interlace:0, page:0, type:1, bsave:".SC4", gs:".SR3"},	// GRAPH SAURUS
	{ext:".SR5", screen_no: 5, interlace:0, page:0, type:1, bsave:".SC5", gs:".SR5"},	// GRAPH SAURUS
	{ext:".SR6", screen_no: 6, interlace:0, page:0, type:1, bsave:".SC6", gs:".SR6"},	// GRAPH SAURUS
	{ext:".SR7", screen_no: 7, interlace:0, page:0, type:1, bsave:".SC7", gs:".SR7"},	// GRAPH SAURUS
	{ext:".SR8", screen_no: 8, interlace:0, page:0, type:1, bsave:".SC8", gs:".SR8"},	// GRAPH SAURUS
	{ext:".SRA", screen_no:10, interlace:0, page:0, type:0, bsave:".S10", gs:".SRA"},	// GRAPH SAURUS
	{ext:".SRC", screen_no:12, interlace:0, page:0, type:0, bsave:".S12", gs:".SRC"},	// GRAPH SAURUS
	{ext:".SRS", screen_no:12, interlace:0, page:0, type:1, bsave:".S12", gs:".SRS"},	// GRAPH SAURUS
	{ext:".R50", screen_no: 5, interlace:1, page:0, type:1, bsave:".S50", gs:".R50"},	// GRAPH SAURUS interlace
    {ext:".R51", screen_no: 5, interlace:1, page:1, type:1, bsave:".S51", gs:".R51"},	// GRAPH SAURUS interlace
	{ext:".R60", screen_no: 6, interlace:1, page:0, type:1, bsave:".S60", gs:".R60"},	// GRAPH SAURUS interlace
    {ext:".R61", screen_no: 6, interlace:1, page:1, type:1, bsave:".S61", gs:".R61"},	// GRAPH SAURUS interlace
	{ext:".R70", screen_no: 7, interlace:1, page:0, type:1, bsave:".S70", gs:".R70"},	// GRAPH SAURUS interlace
    {ext:".R71", screen_no: 7, interlace:1, page:1, type:1, bsave:".S71", gs:".R71"},	// GRAPH SAURUS interlace
	{ext:".R80", screen_no: 8, interlace:1, page:0, type:1, bsave:".S80", gs:".R80"},	// GRAPH SAURUS interlace
    {ext:".R81", screen_no: 8, interlace:1, page:1, type:1, bsave:".S81", gs:".R81"},	// GRAPH SAURUS interlace
	{ext:".RA0", screen_no:10, interlace:1, page:0, type:1, bsave:".SA0", gs:".RA0"},	// GRAPH SAURUS interlace
    {ext:".RA1", screen_no:10, interlace:1, page:1, type:1, bsave:".SA1", gs:".RA1"},	// GRAPH SAURUS interlace
	{ext:".RC0", screen_no:12, interlace:1, page:0, type:1, bsave:".SC0", gs:".RC0"},	// GRAPH SAURUS interlace
    {ext:".RC1", screen_no:12, interlace:1, page:1, type:1, bsave:".SC1", gs:".RC1"},	// GRAPH SAURUS interlace
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
        { no: 0, txw:40, txh:24, name:'TEXT1',      width:240, height:192, bpp:1, page_size:0x04000, }, 
        { no: 0, txw:80, txh:24, name:'TEXT2',      width:480, height:192, bpp:1, page_size:0x04000, }, 
        { no: 1, txw:32, txh:24, name:'GRAPHIC1',   width:256, height:192, bpp:1, page_size:0x04000, }, 
        { no: 2, txw:32, txh:24, name:'GRAPHIC2',   width:256, height:192, bpp:1, page_size:0x04000, }, 
        { no: 3, txw:64, txh:48, name:'MULTICOLOR', width:256, height:192, bpp:1, page_size:0x04000, }, 
        { no: 4, txw:32, txh:24, name:'GRAPHIC3',   width:256, height:192, bpp:1, page_size:0x04000, }, 
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
        { no: 3, txw:64, namsiz:0x00200, patnam:0x0800, patgen:0x0000, patcol:-1    , paltbl:0x2020, s192:0x37FF, s212:0x37FF, }, 
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
        { no: 3, txw:64, spratr:0x0800, sprgen:0x3800, sprcol:-1    , }, 
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
            if (arguments.length > 1) {
                if (width > 40) {
                    no += 1;
                }
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
        p.img_width  = p.width;
        p.img_height = p.height;
        p.interlace_mode = 0;
        p.changeScreen( 5 , 0 );
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
    changeScreen( screen_no, interlace_mode, force_height ) {
        const p = this;

        p.screen_no = screen_no;
        p.mode_info = VDP.getScreenModeSetting( screen_no );
        p.width  = p.mode_info.width;
        p.height = p.mode_info.height;
        if (force_height === undefined) {
            force_height = p.force_height;
        }
        if (force_height) {
            p.height = force_height;
        }
        if (arguments.length >= 2 ) {
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
    cls() {
        this.vram.fill( 0 );
        this.setPalReg16();
    }

    //------------------------
    // 指定したYに対応するアドレスを返す
    //------------------------
    lineAddress( y ) {
        let adr = 0;
        if (this.screen_no >= 5) {
            adr = y * this.mode_info.bpp * this.width / 8;
        } else
        if (this.screen_no == 3) {
            // 64x48ブロック
            // ブロック=4x4ドット
            // 2バイトが2x2ブロック = 8x8ドット
            // 64x2バイトが64x2ブロック
            // int(y/8) * 128 + (y & 1);
            adr = (y >> 3) * 128 + (y & 1);
        } else {
            // 1バイトが 6x8 または 8x8
            // 画面横文字数 バイト が 8 ライン
            adr = (y >> 3) * this.mode_info.txw;
        }
        return this.mode_info.patnam + adr;
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
        if (d.length > limit) {
            p.vram.set( d.subarray(0, limit), offset );
        } else {
            p.vram.set( d, offset );
        }
    }


    //------------------------
    // 描画
    //------------------------
    draw( disp_mode ) {
    	const p = this;

        if (p.canvas) {

            //------------------------
            // メインキャンバス
            //------------------------
            p.canvas.height = p.height * 2;

            var ctx = p.canvas.getContext('2d');
            ctx.imageSmoothingEnabled = false;

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

            //------------------------
            // ページ毎表示キャンバス
            //------------------------
            if (p.page_canvas) {
                let i = 0;
                if (p.interlace_mode || (p.screen_no < 5)) ++i;
                var offscreen = p.offscreen[i];

                for (var pg = 0; pg < p.page_canvas.length; ++pg) {
                    var canvas = p.page_canvas[pg];
                    if (canvas) {
                        canvas.width  = p.canvas.width;
                        canvas.height = p.canvas.height;
                                ctx = canvas.getContext('2d');
                        ctx.imageSmoothingEnabled = false;
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
                canvas.height = 32;

                ctx.fillStyle = "black";
                ctx.fillRect(0,0,canvas.width,canvas.height);

                var w = Math.floor(canvas.width / pal.length);
                for (var i = 0; i < pal.length; ++i) {
                    ctx.fillStyle = pal[i].rgb_string;
                    ctx.fillRect(
                        canvas.width * i / pal.length, 0,
                        w, canvas.height);
                }
                /*
                if (p.screen_no == 6) {
                    ctx.moveTo( canvas.width * 4 / pal.length, canvas.height/2 );
                    ctx.lineTo( canvas.width, canvas.height/2);
                    ctx.lineWidth = 2;
                    ctx.strokeStyle = 'red';
                    ctx.stroke();
                }
                */
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
        case 2:
        case 4:
            p.update_chrgen_x3();
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
            p.update_bitmap8();
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
    update_chrgen_x3() {
    	const p = this;

        if (!p.imgData) {
            console.log('update_chrgen_x3 - this.imgData is null.');
            return;
        }
        let pg_count = 2;//p.interlace_mode + 1;
        let buf = p.imgData.data;
        let d = p.vram;

        let patgen = p.mode_info.patgen;
        let patcol = p.mode_info.patcol;
        const line_size = 4 * vdp.width;

        let txw = p.mode_info.txw;
        let txmask = txw - 1;
        let txshift = 0; while((txw >> txshift) > 1) {txshift ++;}
        let tx_size = txw * p.mode_info.txh;

        let ndx = p.mode_info.patnam;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            for (var i = 0; i < tx_size; ++i) {
                // chr gen view : page 1
                let chr_d = i;
                if (pg == 0) {
                    // main view : page 0
                    chr_d = (d[ndx++] + (i & 0xff00));
                }
                chr_d *= 8;
                let dy = odx
                        + (i & txmask)      // i & 31
                        * 32                // 8px * 4byte
                        + (i >> txshift)    // i / 32
                        * (line_size * 8);  // 8 line

                for(var py = 0; py < 8; ++py, ++chr_d) {
                    let patbit = d[patgen + chr_d];
                    let colset = d[patcol + chr_d];
                    let dx = dy; 
                    for(var px = 0; px < 8; ++px, dx+=4) {
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
            }
            odx += p.width * p.height * 4;
        }
    }
    update_multi_color() {
    	const p = this;

        if (!p.imgData) {
            console.log('update_multi_color - this.imgData is null.');
            return;
        }
        let pg_count = 2;//p.interlace_mode + 1;
        let buf = p.imgData.data;
        let d = p.vram;

        let patnam = p.mode_info.patnam;
        let patgen = p.mode_info.patgen;
        
        let txw = Math.floor(p.mode_info.width  / 8);
        let txh = Math.floor(p.mode_info.height / 8);
        let tx_size = txw * txh;
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
        let pg_count = 2;//p.interlace_mode + 1;
        let buf = p.imgData.data;
        let d = p.vram;
        let sz = p.width / 2 * p.height;
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
    update_bitmap8() {
    	const p = this;

        if (!p.imgData) {
            console.log('update_bitmap16 - this.imgData is null.');
            return;
        }
        let pg_count = 2;//p.interlace_mode + 1;
        let buf = p.imgData.data;
        let d = p.vram;
        let sz = p.width / 4 * p.height;
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
        let pg_count = 2;//p.interlace_mode + 1;
        let buf = p.imgData.data;
        let d = p.vram;
        let sz = p.width * p.height;
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

        let pg_count = 2;//p.interlace_mode + 1;
        let buf = p.imgData.data;
        let d = p.vram;
        let sz = p.width * p.height;
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

        let pg_count = 2;//p.interlace_mode + 1;
        let buf = p.imgData.data;
        let d = p.vram;
        let sz = p.width * p.height;
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

let vdp = new VDP();
//console.log(vdp);

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
        let size = vdp.height * vdp.mode_info.bpp * vdp.width / 8;
        if (with_pal) {
            size = Math.max( vdp.mode_info.palend + 1,  size );
        }

        let out = createBsaveImage( start, size, page, commpress);
        startDownload( out, fname );
    }
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

    let mode_info = VDP.getScreenModeSetting( ext_info.screen_no );
    let force_height = vdp.force_height;
    if ((0 == force_height) && (5 <= mode_info.no))
    {
        // 自動なら画像ピクセルサイズから表示サイズを判断
        if (header.isCompress && ((mode_info.s212 + 1) < dat.length)) {
            // 圧縮形式はパレットを含まないのでline212と比較
            force_height = 256;
        } else
        if ((mode_info.palend + 1) < dat.length) {
            // リニア形式はパレットテーブルを越えているかで判断
            force_height = 256;
        } else {
            force_height = mode_info.height;
        }
    }

    if (ext_info.page && ext_info.interlace &&
         (ext_info.screen_no == vdp.screen_no) &&
         (ext_info.interlace == vdp.interlace_mode) &&
         (force_height == vdp.height)
       ) {
    } else {
        vdp.changeScreen( ext_info.screen_no, ext_info.interlace, force_height );
    }
    if (!ext_info || !ext_info.page) vdp.cls();

    vdp.loadBinary(dat, ext_info.page * vdp.mode_info.page_size);

    // VRAMパレットテーブル読み込み
    if (header.isBinary && !header.isCompress) 
    {
        if (!ext_info.page && (header.end >= vdp.mode_info.palend)) {
            vdp.restorePalette(); 
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
        log_text.innerText = '';
        return false;
    }

    // ファイル名表示
    let file_text = fileText(target_file);
    log_text.innerText = 'read: ' + file_text;

    // 拡張子検査
    let file_ext = getExt(target_file.name);
    let is_pal = isPaletteFile(file_ext);
    let ext_info = getExtInfo(file_ext);
    if (!ext_info && !is_pal)
    {
        // 画像ファイルでなければ無視
        log_text.innerText = '"' + file_text + '": 画像ファイルではありません。';
        return false;
    }

    // カレントファイル表示処理
    if (is_pal) {
        // パレット
        pal_file = LogFile( target_file );
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
        // メイン画像読み込み時はVRAMクリア
        vdp.cls();
    }
    
    // ドロップ可能フラグを一時停止
    drop_avilable = false;
    log_text.innerText = '"' + file_text + '": 読み込み中';

    let config = {};

    // ========================================================
    // ファイル読み込み
    let reader = new FileReader();
    reader.onload = function(f) {
        let u8array = null;
        try {
            u8array = new Uint8Array(f.target.result);
        } catch (e) {
            log_text.innerText = '"' + file_text + '": 読み込みデータに問題があります';
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
            log_text.innerText = '';//'"' + file_text + '": 読み込み完了';
        }
        drop_avilable = true;
        displayCurrentFilename();

        // 読み込み待ちキュー
        if (file_load_que.length)
        {
            openGsFile( file_load_que.shift() );
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
            log_text.innerText = '"' + file_text + '": 読み込みエラーです \n\n'
                                + errmes[reader.error.code];
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

    vdp.initCanvas( canvas_area, palette_area, canvas_page0, canvas_page1 );

    log_text.innerText = '';
    help_guide.innerText = default_log_msg;
    
    displayCurrentFilename();

    // ========================================================
    // イベント：画面引き延ばしモード変更
    // ========================================================
    canvas_area.height = VDP.screen_height;
    const stretch_screen_radio = document.getElementsByName('stretch_screen');
    stretch_screen_radio.forEach(e => { 
        if (e.checked) {
            canvas_area.width = 512 * Number.parseFloat(e.value);
            vdp.draw();
        }
    });
    let onChangeStrechMode = function(event) {
        const e = event.srcElement;
        if (e.checked) {
            canvas_area.width = 512 * Number.parseFloat(e.value);
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
            vdp.changeScreen( vdp.screen_no, vdp.interlace_mode );
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
            tab_title.removeAttribute('open');
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
            tab_title.removeAttribute('open');
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
            startDownload( pald, fname );
        }
    });

    // page 0 bsave
    page0_save_bsave.addEventListener("click",
    function(e) { saveImage( main_file, 0, 0, 1 ); });
    page0_save_bsave_np.addEventListener("click",
    function(e) { saveImage( main_file, 0, 0, 0 ); });
    page0_save_gsrle.addEventListener("click",
    function(e) { saveImage( main_file, 0, 1, 0 ); });

    // page 1 bsave
    page1_save_bsave.addEventListener("click",
    function(e) { saveImage( sub_file, 1, 0, 1 ); });
    page1_save_bsave_np.addEventListener("click",
    function(e) { saveImage( sub_file, 1, 0, 0 ); });
    page1_save_gsrle.addEventListener("click",
    function(e) { saveImage( sub_file, 1, 1, 0 ); });

});

