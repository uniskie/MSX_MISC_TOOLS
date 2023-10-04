const toString = Object.prototype.toString;

// ========================================================
// グローバル変数
// ========================================================

// 初期画面モード
const default_screen_no = 1;

let default_log_html = ''

// 初回（自動でアコーディオンタブを閉じる）
let isFirst = true;

// ドラッグアンドドロップ受付状態
let drop_avilable = true;

// SCREEN 7,8,19,11,12でVRAMインターリーブ接続
let vram_interleave = true;

// パレット反映スイッチ
let palette_use = true;

// スプライト制限モード
let sprite_limit_mode = 0;

// パレットをVRAMから読み込まない
let pal_not_use_vram = 0;

// カラーパレット未使用時にTMS9918Aの色にする
let pal_use_tms9918 = 0;

// パターンジェネレータ：パターンだけ／カラーだけ
let nouse_patgen = false;
let nouse_patcol = false;

// グレースケール
let use_grayscale = false;
let use_grayscale_tmp = false;

// 自動保存モード
let quick_save_mode = 'none';
const quick_save_mode_value = 
 ['none', 'bsave_full', 'bsave_mini', 'gsrle_save'];
 let need_save_all = false;

 // スプライト 透明背景タイプ
 let sprgen_bg_type = 0;

// ========================================================

// ========================================================
// 読み込み済みファイル管理
// ========================================================
function LogFile( file ) {
    return { name: file.name, size: file.size, header: null };
}
const empty_file = { name:'',  size:0, header: null };
let bmp_file = empty_file;
let main_file = empty_file;
let sub_file = empty_file;
let pal_file = empty_file;

// ファイル読み込み待ちキュー
var file_load_que = new Array();

// ========================================================
// クランプ
// ========================================================
function clamp( n, min, max ) {
    n = Math.max( min, Math.min( n, max ) );
    return n;
}

// ========================================================
// 指定値単位になるビットマスクを作成
// ========================================================
function alignMask32( d ) 
{
    return 0xffffffff - (d - 1);
}
// ========================================================
// 指定値未満に収まるビットマスクを作成
// ========================================================
function areaMask32( d ) 
{
    return (d - 1);
}

// ========================================================
// 桁サプレス
// ========================================================
// dec
function zerosup( n, k ) {
    let ns = Math.abs(n).toString(10);
    if (ns.length < k) {
        ns = `0`.repeat(k - ns.length) + ns;
    }
    if (n < 0) return '-' + ns;
    return ns;
}
// hex
function zerosuph( n, k ) {
    let ns = Math.abs(n).toString(16);
    if (ns.length < k) {
        ns = `0`.repeat(k - ns.length) + ns;
    }
    if (n < 0) return '-' + ns;
    return ns;
}

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
// Uint8Array(2) -> Uint16
// ========================================================
function get_u16(d, i) {
    return  d[i] + 
            d[i + 1] * 0x100;
}
// ========================================================
// Uint8Array(4) -> Uint32
// ========================================================
function get_u32(d, i) {
    return  d[i] + 
            d[i + 1] * 0x100 + 
            d[i + 2] * 0x10000 + 
            d[i + 3] * 0x1000000;
}

// ========================================================
// ========================================================
// ラジオスイッチ：チェックされた値を返す
//  in: name - タグのid
// ========================================================
function getCheckedRadioSwitchValue( name )
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
// ラジオスイッチ：指定した値のものをチェック
//  in: name - タグのid
// ========================================================
function setCheckedRadioSwitch( name, value )
{
    let radio_sw = document.getElementsByName( name );
    radio_sw.forEach( e => {
        e.checked = (e.value == value);
    });
}
// ========================================================
// ドロップダウンリスト 要素：クリア
// ========================================================
function removeAllSelectOption( e ) {
    while (e.options.length) {
        e.remove(0);
    }
}
// ========================================================
// ドロップダウンリスト 要素：追加
// ========================================================
function addSelectOption( e, t, v ) {
    let o = new Option( t, v );
    e.options[ e.options.length ] = o;
    return o;
}
// ========================================================
// ドロップダウンリスト 要素：指定値を選択
// ========================================================
function selSelectOption( e, v ) {
    //let old = e.disabled;
    //e.disabled = true;
    for (let i = 0; i < e.options.length; ++i) {
        if (e.options[ i ].value == v) {
            e.selectedIndex = i;
            break;
        }
    }
    //e.disabled = old;
}
// ========================================================
// ========================================================

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

    if (!bmp_file.name.length &&
        !main_file.name.length && 
        !sub_file.name.length) 
    {
        tab_save_all.style.display = 'none';
    } else {
        tab_save_all.style.display = 'block';
    }

    if (!bmp_file.name.length &&
        !main_file.name.length && 
        !pal_file.name.length ) 
    {
        pal_save.style.display = 'none';
    } else {
        pal_save.style.display = 'inline-block';
    }

    detail_page0.width = canvas_page0.width;
    detail_page1.width = canvas_page1.width;
    detail_page2.width = canvas_page2.width;
    detail_page3.width = canvas_page3.width;

    tab_detail_chrgen.width = canvas_patgen.width;
    tab_detail_sprgen.width = canvas_sprgen.width;

    if (bmp_file.name.length) {
        filename_area.textContent = fileText(bmp_file);
        filename_area2.textContent = '';
        filename_area3.textContent = '';
        detail_page0_file.textContent = fileText(bmp_file);
        if (bmp_file.header) {
            detail_page0_spec.textContent = 
            `[START:0x${bmp_file.header.start.toString(16)} END:0x${bmp_file.header.end}]`;
        } else {
            detail_page0_spec.textContent = '';
        }
        page0_save_bsave   .disabled = false;
        page0_save_bsave_np.disabled = false;
        page0_save_gsrle   .disabled = false;
        page0_save_group   .style.display ="inline-block";

        detail_page0_spec.textContent = '';

        //detail_page1.style.display ="inline-block";
        page1_save_bsave   .disabled = false;
        page1_save_bsave_np.disabled = false;
        page1_save_gsrle   .disabled = false;
        page1_save_group   .style.display ="inline-block";
    } else {
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
            page0_save_group   .style.display ="inline-block";
        } else {
            filename_area.textContent = '';
            detail_page0_file.textContent = '';
            detail_page0_spec.textContent = '';
            page0_save_bsave   .disabled = true;
            page0_save_bsave_np.disabled = true;
            page0_save_gsrle   .disabled = true;
            page0_save_group   .style.display ="none";
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
            detail_page1.style.display ="inline-block";
            page1_save_bsave   .disabled = false;
            page1_save_bsave_np.disabled = false;
            page1_save_gsrle   .disabled = false;
            page1_save_group   .style.display ="inline-block";
        } else {
            filename_area2.textContent = '';
            detail_page1_file.textContent = '';
            detail_page1_spec.textContent = '';
            detail_page1.style.display ="none";
            page1_save_bsave   .disabled = true;
            page1_save_bsave_np.disabled = true;
            page1_save_gsrle   .disabled = true;
            page1_save_group   .style.display ="none";
        }
    }

    if (vdp.screen_no < 5) {
        if (vdp.r25_sp2 && vdp.screen_no) {
            detail_page1.style.display ="inline-block";
        } else {
            detail_page1.style.display ="none";
        }
        detail_page2.style.display ="none";
        detail_page3.style.display ="none";
    } else {
        if (vdp.interlace_mode || bmp_file.name.length) {
            detail_page1.style.display ="inline-block";
        } else {
            detail_page1.style.display ="none";
        }
        if (bmp_file.name.length) {
            switch (vdp.screen_no) {
                case 5:
                case 6:
                case 9:
                    detail_page2.style.display ="inline-block";
                    detail_page3.style.display ="inline-block";
                    break;
                default:
                    detail_page2.style.display ="none";
                    detail_page3.style.display ="none";
                    break;
            }
        } else {
            detail_page2.style.display ="none";
            detail_page3.style.display ="none";
        }
    }

    if (vdp.screen_no < 5) {
        tab_detail_chrgen.style.display ="inline-block";
    } else {
        tab_detail_chrgen.style.display ="none";
    }

    if (vdp.screen_no > 0) {
        tab_detail_sprgen.style.display ="inline-block";
    } else {
        tab_detail_sprgen.style.display ="none";
    }

    displayPaletteInfo();
    displayCurrentScreenMode();
}
function displayPaletteInfo()
{
    if (!palette_use) {
        label_pal_file.textContent = '【カラーパレット無効】'
        detail_pal_file.textContent =  '';
    } else {
        label_pal_file.textContent = '【カラーパレット】'
        if (pal_file.name.length) {
            filename_area3.textContent = fileText(pal_file);
            detail_pal_file.textContent = fileText(pal_file);
        } else
        if (bmp_file.name.length) {
            filename_area3.textContent = '';
            detail_pal_file.textContent = fileText(bmp_file);
        } else {
            filename_area3.textContent = '';
            detail_pal_file.textContent =  '（VRAMパレットテーブル）';
        }
    }
}
// ========================================================
// 現在の画面モード情報
// ========================================================
function displayCurrentScreenMode() {
    // 画面設定表示
    sel_screen_no.selectedIndex = vdp.mode_info.idx;
    screen_interlace_chk.checked = vdp.interlace_mode;
    if (vdp.screen_no < 5) {
        //sel_disp_page.disabled = true;
        let page_size = vdp.mode_info.page_size;
        let page = Math.floor(vdp.base.patnam / page_size);
        //if (page != Math.floor(vdp.base.patgen / page_size)) page = -1;
        //if (0 <= vdp.base.patcol) {
        //    if (page != Math.floor(vdp.base.patcol / page_size)) page = -1;
        //}
        sel_disp_page.selectedIndex = page;
        //sel_disp_page.disabled = false;
    } else {
        sel_disp_page.selectedIndex = vdp.disp_page;
    }
    detail_screen_mode_name.textContent = `[${vdp.mode_info.name}]`;
    detail_screen_width.textContent  = `[W:${vdp.width}]`;
    detail_screen_height.textContent = `[H:${vdp.height}]`;
    if (vdp.interlace_mode) detail_interlace.textContent = '[Interlaced]';
    else                    detail_interlace.textContent = '[No-Interlace]';

    displayTableBaseInfo();
    displaySpriteInfo();
    displayScrollInfo();
}

// スクロール情報表示
function displayScrollInfo()
{
    detail_vscroll.textContent = `[▲▼VScroll:${zerosup(vdp.vscroll, 3)}]`;
    detail_hscroll.textContent = `[◀▶HScroll:${zerosup(vdp.hscroll, 3)}]`;
    hscroll_mask_chk.checked = (0 != vdp.r25_msk);
    hscroll_2page_chk.checked = (0 != vdp.r25_sp2);
}
// テーブルベースアドレス表示
function displayTableBaseInfo() {
    if (vdp.base.patcol < 0) {
        detail_chrgen_spec.innerText = 
        `[name:0x${zerosuph(vdp.base.patnam, 5)}] `+
        `[gen:0x${zerosuph(vdp.base.patgen, 5)}]`;
    } else {
        detail_chrgen_spec.innerText = 
        `[name:0x${zerosuph(vdp.base.patnam, 5)}] `+
        `[gen:0x${zerosuph(vdp.base.patgen, 5)}] `+
        `[color:0x${zerosuph(vdp.base.patcol, 5)}]`;
    }

    if (vdp.base.sprcol < 0) {
        detail_sprgen_spec.innerText = 
        `[atr:0x${zerosuph(vdp.base.spratr, 5)}] `+
        `[pat:0x${zerosuph(vdp.base.sprpat, 5)}]`;
    } else {
        detail_sprgen_spec.innerText = 
        `[atr:0x${zerosuph(vdp.base.spratr, 5)}] `+
        `[pat:0x${zerosuph(vdp.base.sprpat, 5)}] `+
        `[color:0x${zerosuph(vdp.base.sprcol, 5)}]`;
    }
    selectTableBaseOptions();

    patgen_chk.checked = !nouse_patgen;
    patcol_chk.checked = !nouse_patcol;

    switch (vdp.screen_no) {
    case 1:
    case 2:
    case 4:
        patgen_chk.style.display = "inline-block";
        patcol_chk.style.display = "inline-block";
        break;
    default:
        patgen_chk.style.display = "none";
        patcol_chk.style.display = "none";
        break;
    }
}
// テーブルベースアドレス ドロップダウンリストの自動選択
function selectTableBaseOptions()
{
    let block_size = vdp.mode_info.block_size;
    let page_mask = block_size - 1;
    selSelectOption( sel_patnam_ofs , vdp.base.patnam & page_mask );
    selSelectOption( sel_patnam_page, Math.floor(vdp.base.patnam / block_size));
    selSelectOption( sel_patgen_ofs ,            vdp.base.patgen & page_mask );
    selSelectOption( sel_patgen_page, Math.floor(vdp.base.patgen / block_size));
    if (vdp.base.patcol < 0) {
        sel_patcol_ofs.selectedIndex = -1;
        sel_patcol_page.selectedIndex = -1;
    } else {
        selSelectOption( sel_patcol_ofs ,            vdp.base.patcol & page_mask );
        selSelectOption( sel_patcol_page, Math.floor(vdp.base.patcol / block_size));
    }
    selSelectOption( sel_spratr_ofs ,            vdp.base.spratr & page_mask );
    selSelectOption( sel_spratr_page, Math.floor(vdp.base.spratr / block_size));
    selSelectOption( sel_sprpat_ofs ,            vdp.base.sprpat & page_mask );
    selSelectOption( sel_sprpat_page, Math.floor(vdp.base.sprpat / block_size));
}
function displaySpriteInfo() {
    if (vdp.sprite_disable) detail_sprite_on.textContent = '[SPRITE OFF]';
    else 
    if (vdp.sprite_double) {
        if (vdp.sprite16x16 )   detail_sprite_on.textContent = '[SPRITE 16x16 x2]';
        else                    detail_sprite_on.textContent = '[SPRITE 8x8 x2]';
    } else {
        if (vdp.sprite16x16 )   detail_sprite_on.textContent = '[SPRITE 16x16]';
        else                    detail_sprite_on.textContent = '[SPRITE 8x8]';
    }

    // スプライト無効/有効
    sprite_use_chk.checked = !vdp.sprite_disable;
    if (vdp.sprite_disable) {
        label_sprite_use.innerText = 'Sprite Off';
    } else {
        label_sprite_use.innerText = 'Sprite On';
    }

    // スプライト設定
    sel_sprite_mode.selectedIndex =
        (vdp.sprite16x16 << 1) | vdp.sprite_double;
}

// ========================================================
// ベースアドレス ドロップダウンリスト更新
// ========================================================
function updateBaseAddressList()
{
    if (!vdp) return;
    if (!sel_spratr_page) return;

    function addLists( t, pe, e, funcidx, funcn, def_v ) {
        let block_size = vdp.mode_info.block_size;
        let page = parseInt(def_v / block_size);
        let def = def_v - page * block_size;

        removeAllSelectOption( pe );
        removeAllSelectOption( e );

        if (vdp.screen_no < 5) {
            for (let n = 0; n < vdp.max_block; ++n ) {
                addSelectOption( pe, `0x${(n * 0x4000).toString(16)}+`, n );
            }
        } else {
            for (let n = 0; n < vdp.max_block; ++n ) {
                addSelectOption( pe, `Page ${n}`, n );
            }
        }

        let selectedIndex = -1;
        let a = -1;
        for (let n = 0;; ++n) {
            a = funcidx( n );
            if (a < 0)break;
            if (block_size <= a) break;
            t = `0x${a.toString(16)}`;
            let i = addSelectOption( e, t, a );
            if (a == def) {
                selectedIndex = n;
            }
        }
        e.selectedIndex = selectedIndex;

        // 戻す
         pe.selectedIndex = page;
        funcn( def_v );
    }

    // ========================================================
    // CHARACTER GENERATOR TABLE
    // ========================================================
    sel_patnam_page.disabled = true;
    sel_patnam_ofs .disabled = true;
    sel_patgen_page.disabled = true;
    sel_patgen_ofs .disabled = true;
    sel_patcol_page.disabled = true;
    sel_patcol_ofs .disabled = true;

    addLists( 'PatNam:', 
        sel_patnam_page, 
        sel_patnam_ofs,  
        n => { return vdp.setPatternNameTableIdx(n); }, 
        n => { return vdp.setPatternNameTable(n); }, 
        vdp.base.patnam );
    addLists( 'PatGen:', 
        sel_patgen_page, 
        sel_patgen_ofs,  
        n => { return vdp.setPatternGeneratorTableIdx(n); },
        n => { return vdp.setPatternGeneratorTable(n); },
        vdp.base.patgen );
     addLists( 'PatCol:', 
        sel_patcol_page, 
        sel_patcol_ofs,  
        n => { return vdp.setPatternColorTableIdx(n); },
        n => { return vdp.setPatternColorTable(n); },
        vdp.base.patcol );
    if (vdp.base.patcol < 0) {
        sel_patcol_group.style.display = "none";
    } else {
        sel_patcol_group.style.display = "inline-block";
    }
 
    sel_patnam_page.disabled = false;
    sel_patnam_ofs .disabled = false;
    sel_patgen_page.disabled = false;
    sel_patgen_ofs .disabled = false;
    sel_patcol_page.disabled = false;
    sel_patcol_ofs .disabled = false;
    
    // ========================================================
    // SPRITE TABLE
    // ========================================================
    sel_spratr_page.disabled = true;
    sel_spratr_ofs .disabled = true;
    sel_sprpat_page.disabled = true;
    sel_sprpat_ofs .disabled = true;

    addLists( 'SprAtr:', 
        sel_spratr_page, 
        sel_spratr_ofs,  
        n => { return vdp.setSpriteAttributeTableIdx(n); }, 
        n => { return vdp.setSpriteAttributeTable(n); }, 
        vdp.base.spratr );
    addLists( 'SprPtr:', 
        sel_sprpat_page, 
        sel_sprpat_ofs,  
        n => { return vdp.setSpritePatternTableIdx(n); },
        n => { return vdp.setSpritePatternTable(n); },
        vdp.base.sprpat );

    sel_spratr_page.disabled = false;
    sel_spratr_ofs .disabled = false;
    sel_sprpat_page.disabled = false;
    sel_sprpat_ofs .disabled = false;

    // ========================================================
    // Display Page
    // ========================================================
    sel_disp_page.disabled   = true;
    removeAllSelectOption( sel_disp_page );
    for (let n = 0; n < vdp.max_page; ++n ) {
        addSelectOption( sel_disp_page, `Page ${n}`, n );
    }
    if (vdp.screen_no < 5) {
        let page_size = vdp.mode_info.page_size;
        let page = Math.floor(vdp.base.patnam / page_size);
        if (page != Math.floor(vdp.base.patgen / page_size)) page = -1;
        if (page != Math.floor(vdp.base.patcol / page_size)) page = -1;
        sel_disp_page.selectedIndex = page;
    } else {
        sel_disp_page.selectedIndex = vdp.disp_page;
    }
    sel_disp_page.disabled   = false;
}

// ========================================================
// 拡張子情報
// ========================================================
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
	{ext:'.GE5', screen_no: 5, interlace:0, page:0, type:0, bsave:'.GE5', gs:'.GE5'},	// DD CLUB
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
    {ext:'.VRM', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.VRM', gs:'.GSR'},	// RAWイメージ 新10倍カートリッジ
    {ext:'.SPR', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.SPR', gs:'.SPR'},	// スプライト
    {ext:'.SPC', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.SPC', gs:'.SPC'},	// スプライトカラー
    {ext:'.NAM', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.NAM', gs:'.NAM'},	// SC2 パターンネーム
    {ext:'.COL', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.COL', gs:'.COL'},	// SC2 パターンカラー
    {ext:'.GEN', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.GEN', gs:'.GEN'},	// SC2 パターンジェネレータ
    {ext:'.PAT', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.PAT', gs:'.PAT'},	// SC2 パターンジェネレータ

    {ext:'.NM' , screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.NM' , gs:'.NM' },	// SC2 パターンネーム
    {ext:'.CL' , screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.CL' , gs:'.CL' },	// SC2 パターンカラー
    {ext:'.GN' , screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.GN' , gs:'.GN' },	// SC2 パターンジェネレータ

    {ext:'.CL0', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.CL0', gs:'.CL0'},	// SC2 パターンカラー
    {ext:'.CL1', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.CL1', gs:'.CL1'},	// SC2 パターンカラー
    {ext:'.CL2', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.CL2', gs:'.CL2'},	// SC2 パターンカラー

    {ext:'.GN0', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.GN0', gs:'.GN0'},	// SC2 パターンジェネレータ
    {ext:'.GN1', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.GN1', gs:'.GN1'},	// SC2 パターンジェネレータ
    {ext:'.GN2', screen_no:-1, interlace:-1, page:-1, type:0, bsave:'.GN2', gs:'.GN2'},	// SC2 パターンジェネレータ

    {ext:'.BMP', screen_no:-1, interlace:-1, page:-1, type:2, bsave:'.VRM', gs:'.GSR'},	// RAWイメージ OpenMSX vram2bmp の非圧縮BMP
    {ext:'.SCR', screen_no:-1, interlace:-1, page:-1, type:2, bsave:'.SCR', gs:'.GSR'},	// RAWイメージ
    {ext:'.GSR', screen_no:-1, interlace:-1, page:-1, type:2, bsave:'.SCR', gs:'.GSR'},	// RAWイメージ
    
    {ext:'.CPY', screen_no:-1, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文）
    {ext:'.CP5', screen_no: 5, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文）
    {ext:'.CP6', screen_no: 6, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文）
    {ext:'.CP7', screen_no: 7, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文）
    {ext:'.CP8', screen_no: 8, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文）
    {ext:'.CPA', screen_no:10, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文）
    {ext:'.CPC', screen_no:12, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文）

    {ext:'.GL5', screen_no: 5, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文/グラフサウルス拡張子）
    {ext:'.GL6', screen_no: 6, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文/グラフサウルス拡張子風）
    {ext:'.GL7', screen_no: 7, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文/グラフサウルス拡張子）
    {ext:'.GL8', screen_no: 8, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文/グラフサウルス拡張子）
    {ext:'.GLA', screen_no:10, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文/グラフサウルス拡張子風）
    {ext:'.GLC', screen_no:12, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文/グラフサウルス拡張子風）
    {ext:'.GLS', screen_no:12, interlace:-1, page:-1, type:3, bsave:'.VRM', gs:'.CPR'},	// 範囲画像（BASIC COPY文/グラフサウルス拡張子）

    // 仮対応：スクリーン0、1
//	{ext:'.SC1', screen_no: 1,         interlace:0, page:0, type:0, bsave:'.SC1', gs:'.SR1'},	// BSAVE
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
// ========================================================
// BSAVE/GSファイルヘッダー
// ========================================================
class BinHeader {
    [Symbol.toStringTag] = 'BinHeader';
    static get HEADER_SIZE() { return 7; }
    static get HEAD_ID_LINEAR() { return 0xFE; } // BSAVE/GS LINEAR
    static get HEAD_ID_COMPRESS() { return 0xFD; } // #GS RLE COMPLESS

    constructor( d ) {
        this.id    = 0;
        this.start = 0;
        this.end   = 0;
        this.run   = 0;

        if (d !== undefined) {
            if (d.constructor == Uint8Array) {
                this.set( d );
            } else
            if (d.constructor == BinHeader) {
                this.id    = d.id   ;
                this.start = d.start;
                this.end   = d.end  ;
                this.run   = d.run  ;
            }
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
        // BSAVEのヘッダで示すサイズが0x10000以上だと
        // BLOADで異常をきたすので0xffffに抑える
        // （STARTが0のときENDは0xFFFEが最大）
        // （ヘッダのENDを見ずにファイルサイズをみると
        //   最後まで読み込める）
        let size = Math.min(0xfffe, this.end -this.start);
        let end = this.start + this.end;
        return Uint8Array.from([
            this.id, 
            this.start & 255,
            (this.start >> 8) & 255,
            end & 255,
            (end >> 8) & 255,
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

// ========================================================
// RGB888を輝度に変換
// ========================================================
function rgb_to_brightness(r,g,b) {
    const t = [0.299, 0.587, 0.114];
    //const t = [0.3, 0.6, 0.1];
    return Math.floor(t[0] * r + t[1] * g + t[2] * b);
}

// ========================================================
// RGB888をスタイルカラー文字列に変換
// ========================================================
function rgb_string(r) {
    return `rgb( ${r[0]}, ${r[1]}, ${r[2]} )`;
}

// ========================================================
// カラーパレット
// ========================================================
class PaletteEntry {
    [Symbol.toStringTag] = 'PaletteEntry';
    /*
        MSX palette (r,g,b)=(7,7,7)
        16bit - 0grb
        8bit - rb, 0g
    */
    constructor( r, g, b ) {
        this.r = 0;
        this.g = 0;
        this.b = 0;
        if (r === undefined) {
            // 何もしない
        } else
        if (arguments.length == 1) {
            if (r.constructor === PaletteEntry) {
            	this.copy( r );
            } else {
	            this.word = r;
	        }
        } else
        if (arguments.length == 3) {
            this.set(r, g, b);
        }
    }
    copy( s ) {
        this.r = s.r;
        this.g = s.g;
        this.b = s.b;
    }
    //--------------------------------
    // MSX用 R3, G3, B3で設定
    //--------------------------------
    set( r, g, b ) {
        this.r = r  & 7;
        this.g = g  & 7;
        this.b = b  & 7;
    }
    //--------------------------------
    // MSX用 16bit値で設定
    //--------------------------------
    set word( w ) 
    {
        this.r = (w >> 4) & 7;
        this.g = (w >> 8) & 7;
        this.b = (w >> 0) & 7;
    }
    //--------------------------------
    // MSX用 16bit値を取得
    //--------------------------------
    get word() {
        return this.r * 16 + this.g * 256 + this.b;
    }
    //--------------------------------
    // MSX用 8bit値*2を取得
    //--------------------------------
    get bytes() {
        return [ this.r * 16 + this.b, this.g ];
    }
    //--------------------------------
    // R8,G8,B8で指定
    //--------------------------------
    setRgb888(r,g,b) {
        this.r = clamp(Math.floor((r + 4) * 7 / 255), 0, 7);
        this.g = clamp(Math.floor((g + 4) * 7 / 255), 0, 7);
        this.b = clamp(Math.floor((b + 4) * 7 / 255), 0, 7);
    }
    //--------------------------------
    // RGBA Uint8Array(4)
    //--------------------------------
    get rgba() {
        return Uint8Array.from([
            clamp(Math.floor(this.r * 255 / 7), 0, 255),
            clamp(Math.floor(this.g * 255 / 7), 0, 255),
            clamp(Math.floor(this.b * 255 / 7), 0, 255),
            0xff]);
    }
    //--------------------------------
    // fillStileなどに渡す文字列
    //--------------------------------
    get rgb_string() {
        return rgb_string( this.rgba );
    }
    //--------------------------------
    // 輝度
    //--------------------------------
    get brightness() {
        const rgba = this.rgba;
        return rgb_to_brightness(rgba[0], rgba[1], rgba[2]);
    }
    get brightness_string() {
        return rgb_string( this.brightness );
    }

};
class Palette {
    [Symbol.toStringTag] = 'PaletteEntry';
    constructor( entry_count, d ) {
        const p = this;
        p.color = new Array( entry_count );
        p.rgba = new Array( entry_count );
        p.gray = new Array( entry_count );
        p.setPalette( d );
    }
    setPalette( d ) {
        const p = this;
        let entry_count = p.color.length;
        if (d === undefined) {
            if (entry_count == 16) {
                d = VDP.msx2pal;    // MSX2カラーパレット
                //d = VDP.msx1fpal;   // MSX1風カラーパレット
                for (var i = 0; i <p.color.length; ++i) {
                    p.color[i] = new PaletteEntry( d[i] );
                }
            } else 
            if (entry_count == 256) {
                // screen8 color : GGGRRRBB
                for (var i = 0; i < entry_count; ++i) {
                    p.color[i] = new PaletteEntry(
                        (i >> 2) & 7, i >> 5, (i << 1) & 7);
                }
            } else {
                for (var i = 0; i <p.color.length; ++i) {
                    p.color[i] = new PaletteEntry( 0, 0, 0 );
                }
            }
        } else
        if (d.constructor === Uint8Array) {
            for (var i = 0; i < p.color.length; ++i) {
                p.color[i] = new PaletteEntry( d[i*2] + d[i*2+1] * 256 );
            }
        } else
        {
            for (var i = 0; i < p.color.length; ++i) {
                p.color[i] = new PaletteEntry( d[i] );
            }
        }
        p.makeRgba();
    }
    makeRgba() {
        const p = this;
        for (var i = 0; i < p.color.length; ++i) {
            p.rgba[i] = p.color[i].rgba;
        }
        let b;
        for (var i = 0; i < p.color.length; ++i) {
            b = p.color[i].brightness;
            p.gray[i] = [b, b, b, 255];
        }
        return p.rgba;
    }
    setRgba( ar ) {
        const p = this;
        for (var i = 0; i < p.color.length; ++i) {
            p.rgba[i] = ar[i];
        }
        return p.rgba;
    }
    getPalTbl() {
        const p = this;
        let d = new Uint8Array( p.color.length * 2 );
        let idx = 0;
        for (var i = 0; i < p.color.length; ++i, idx+=2) {
            d[idx + 0] = p.color[i].word & 255;
            d[idx + 1] = (p.color[i].word >> 8) & 255;
        }
        return d;
    }
};

// ========================================================
// VDP class
// ========================================================
class VDP {
    [Symbol.toStringTag] = 'VDP';
    /*
        MSX VDP
    */
    // ========================================================
    // [static] プロパティ＆メソッド
    // =======================================================
	static get aspect_ratio () { return 1.177; } // openMSX 3x:904 2x:603 1x:301
	static get aspect_ratio2() { return 1.133; }  // konamiman (4/564.8522)/(3/480) = 1.133039756

    static get render_width () { return 512; }
	static get render_height() { return 512; }

    static get sprite_plane_width () { return 256; }
	static get sprite_plane_height() { return 256; }

	static get vram_size() { return 0x20000; }	// 128 * 1024;
    static get palette_count() { return 16; }
    static get scan_line_count() { return 256; }

    // ========================================================
    // [static] カラーパレット値
    // ========================================================
    // MSX2標準カラーパレット 0x0GRB
    static get msx2pal() { return Uint16Array.from([
        0x0000,0x0000,0x0611,0x0733, 0x0117,0x0327,0x0151,0x0627,
        0x0171,0x0373,0x0661,0x0664, 0x0411,0x0265,0x0555,0x0777,
    ]); }
    // SCREEN8 SPRITE カラーパレット
    static get sc8spr_pal() { return Uint16Array.from([
        0x0000,0x0002,0x0030,0x0032, 0x0300,0x0302,0x0330,0x0332,
        0x0470,0x0007,0x0070,0x0077, 0x0700,0x0707,0x0770,0x0777,  
    ]); }
    // MSX1風カラーパレット
    static get msx1fpal() { return Uint16Array.from([
        0x0000,0x0000,0x0533,0x0644, 0x0237,0x0347,0x0352,0x0536,
        0x0362,0x0463,0x0653,0x0664, 0x0421,0x0355,0x0555,0x0777,
    ]); }
    // TMS9918Aカラーパレット RGB888
    static get tms9918pal8888() { return Array.from(
        [
            Uint8Array.from([   0,   0,   0, 255 ]),
            Uint8Array.from([   0,   0,   0, 255 ]),
            Uint8Array.from([  79, 176,  69, 255 ]),
            Uint8Array.from([ 129, 202, 119, 255 ]),
            Uint8Array.from([  95,  81, 237, 255 ]),
            Uint8Array.from([ 129, 116, 255, 255 ]),
            Uint8Array.from([ 173, 101,  77, 255 ]),
            Uint8Array.from([ 103, 195, 228, 255 ]),
            Uint8Array.from([ 204, 110,  80, 255 ]),
            Uint8Array.from([ 240, 146, 116, 255 ]),
            Uint8Array.from([ 193, 202,  81, 255 ]),
            Uint8Array.from([ 209, 215, 129, 255 ]),
            Uint8Array.from([  72, 156,  59, 255 ]),
            Uint8Array.from([ 176, 104, 190, 255 ]),
            Uint8Array.from([ 204, 204, 204, 255 ]),
            Uint8Array.from([ 255, 255, 255, 255 ]),
        ]);
    }
    // ========================================================
    // [static] 画面モード別 スペック
    // ========================================================
    static get screen_mode_spec1() { return [
        { no: 0, txw:40, txh:24, name:'TEXT1',      width:240, height:192, bpp:0, block_size:0x04000, page_size:0x08000, }, 
        { no: 0, txw:80, txh:24, name:'TEXT2',      width:480, height:192, bpp:0, block_size:0x04000, page_size:0x08000, }, 
        { no: 1, txw:32, txh:24, name:'GRAPHIC1',   width:256, height:192, bpp:0, block_size:0x04000, page_size:0x08000, }, 
        { no: 2, txw:32, txh:24, name:'GRAPHIC2',   width:256, height:192, bpp:0, block_size:0x04000, page_size:0x08000, }, 
        { no: 3, txw:32, txh:24, name:'MULTICOLOR', width:256, height:192, bpp:0, block_size:0x04000, page_size:0x08000, }, 
        { no: 4, txw:32, txh:24, name:'GRAPHIC3',   width:256, height:192, bpp:0, block_size:0x04000, page_size:0x08000, }, 
        { no: 5, txw:32, txh:26, name:'GRAPHIC4',   width:256, height:212, bpp:4, block_size:0x08000, page_size:0x08000, }, 
        { no: 6, txw:64, txh:26, name:'GRAPHIC5',   width:512, height:212, bpp:2, block_size:0x08000, page_size:0x08000, }, 
        { no: 7, txw:64, txh:26, name:'GRAPHIC6',   width:512, height:212, bpp:4, block_size:0x10000, page_size:0x10000, }, 
        { no: 8, txw:32, txh:26, name:'GRAPHIC7',   width:256, height:212, bpp:8, block_size:0x10000, page_size:0x10000, }, 
        { no: 9, txw:64, txh:26, name:'GRAPHIC8',   width:512, height:212, bpp:2, block_size:0x08000, page_size:0x08000, }, 
        { no:10, txw:32, txh:26, name:'YAE',        width:256, height:212, bpp:8, block_size:0x10000, page_size:0x10000, }, 
        { no:11, txw:32, txh:26, name:'YAE',        width:256, height:212, bpp:8, block_size:0x10000, page_size:0x10000, }, 
        { no:12, txw:32, txh:26, name:'YJK',        width:256, height:212, bpp:8, block_size:0x10000, page_size:0x10000, }, 
    ]; }
    // ========================================================
    // [static] 画面モード別キャラジェネ設定
    // ========================================================
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
    // ========================================================
    // [static ]画面モード別スプライト設定
    // ========================================================
    static get screen_mode_spec3() { return [
    	//                                                               
        { no: 0, txw:40, spratr:-1    , sprpat:-1    , sprcol:-1    , }, 
        { no: 0, txw:80, spratr:-1    , sprpat:-1    , sprcol:-1    , }, 
        { no: 1, txw:32, spratr:0x1B00, sprpat:0x3800, sprcol:-1    , }, 
        { no: 2, txw:32, spratr:0x1B00, sprpat:0x3800, sprcol:-1    , }, 
        { no: 3, txw:32, spratr:0x1B00, sprpat:0x3800, sprcol:-1    , }, 
        { no: 4, txw:32, spratr:0x1E00, sprpat:0x3800, sprcol:0x1C00, }, 
        { no: 5, txw:32, spratr:0x7600, sprpat:0x7800, sprcol:0x7400, }, 
        { no: 6, txw:64, spratr:0x7600, sprpat:0x7800, sprcol:0x7400, }, 
        { no: 7, txw:64, spratr:0xFA00, sprpat:0xF000, sprcol:0xF800, }, 
        { no: 8, txw:32, spratr:0xFA00, sprpat:0xF000, sprcol:0xF800, }, 
        { no: 9, txw:64, spratr:0x7600, sprpat:0x7800, sprcol:0x7400, }, 
        { no:10, txw:32, spratr:0xFA00, sprpat:0xF000, sprcol:0xF800, }, 
        { no:11, txw:32, spratr:0xFA00, sprpat:0xF000, sprcol:0xF800, }, 
        { no:12, txw:32, spratr:0xFA00, sprpat:0xF000, sprcol:0xF800, }, 
    ]; }
    // ========================================================
    // [static] 画面モード別 アドレス指定可能単位
    // ========================================================
    static get screen_mode_spec4() { return [
        { no: 0, txw:40, u_patnam:0x00400, u_patgen:0x0800, u_patcol:-1    , }, 
        { no: 0, txw:80, u_patnam:0x01000, u_patgen:0x0800, u_patcol:0x0200, }, 
        { no: 1, txw:32, u_patnam:0x00400, u_patgen:0x0800, u_patcol:0x0040, }, 
        { no: 2, txw:32, u_patnam:0x00400, u_patgen:0x0800, u_patcol:0x2000, }, 
        { no: 3, txw:32, u_patnam:0x00400, u_patgen:0x0800, u_patcol:-1    , }, 
        { no: 4, txw:32, u_patnam:0x00400, u_patgen:0x0800, u_patcol:0x2000, }, 
        { no: 5, txw:32, u_patnam:0x08000, u_patgen:-1    , u_patcol:-1    , }, 
        { no: 6, txw:64, u_patnam:0x08000, u_patgen:-1    , u_patcol:-1    , }, 
        { no: 7, txw:64, u_patnam:0x10000, u_patgen:-1    , u_patcol:-1    , }, 
        { no: 8, txw:32, u_patnam:0x10000, u_patgen:-1    , u_patcol:-1    , }, 
        { no: 9, txw:64, u_patnam:0x08000, u_patgen:-1    , u_patcol:-1    , }, 
        { no:10, txw:32, u_patnam:0x10000, u_patgen:-1    , u_patcol:-1    , }, 
        { no:11, txw:32, u_patnam:0x10000, u_patgen:-1    , u_patcol:-1    , }, 
        { no:12, txw:32, u_patnam:0x10000, u_patgen:-1    , u_patcol:-1    , }, 
    ]; }
    // ========================================================
    // [static] 画面モード別 設定
    // ========================================================
    static getScreenModeSettingByIdx( idx ) {
        if ((idx < 0) || (VDP.screen_mode_spec1.length <= idx)) {
            return null;
        }
    	// 結合して返す
    	let info = { 
            idx: idx
            , ...VDP.screen_mode_spec1[idx]
            , ...VDP.screen_mode_spec2[idx]
            , ...VDP.screen_mode_spec3[idx] 
            , ...VDP.screen_mode_spec4[idx] 
        };
        // VRAMパレットエントリエンド
        info.palend = info.paltbl + 32 -1;
        info.sPal = Math.max(info.s212, info.palend);
        return info;
    }
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
        return VDP.getScreenModeSettingByIdx(no);
    }
    // ========================================================
    // パブリックフィールド プロパティ
    // ========================================================
    //------------------------
    // VRAM
    //------------------------
    vram            = new Uint8Array( VDP.vram_size );
    //------------------------
    // 表示ページ
    //------------------------
    disp_page       = 0;        
    //------------------------
    // カラーパレット
    //------------------------
    // default color palette
    pal_def = new Palette( VDP.palette_count, VDP.msx2pal );
    // current color palette
    palette = new Palette( VDP.palette_count, VDP.msx2pal );
    // screen8 color palette (Bitmap)
    pal256 = new Palette( 256 );
    // screen8 color palette (Sprite)
    pal8spr = new Palette( VDP.palette_count, VDP.sc8spr_pal );
    // black/white color palette
    pal_bf = new Palette( VDP.palette_count, 
        Uint16Array.from([
            0,0xfff,0xfff,0xfff,0xfff,0xfff,0xfff,0xfff,0xfff,0xfff,0xfff,0xfff,0xfff,0xfff,0xfff,0xfff
        ]) );
    //------------------------
    // canvas
    //------------------------
    cs = {
        canvas:         null,
        pal_canvas:     null,
        page_canvas:    [null, null, null, null],
        patgen_canvas:  null,
        sprgen_canvas:  null
    };
    offscreen = [null, null, null]; // disp, work, spr
    imgData   = null;
    sprData   = null;
    //------------------------
    // screen 情報
    //------------------------
    mode_info       = null;
    screen_no       = default_screen_no;
    width           = 256;
    height          = 192;
    interlace_mode  = 0;
    disp_page       = 0;
    max_page        = 1;
    max_block       = 1;
    canvas_max_page = 1;
    img_width       = VDP.render_width;
    img_height      = VDP.render_height;
    // 特殊処理
    auto_height     = 0;
    force_height    = 0;
    aspect_ratio    = VDP.aspect_ratio;
    //------------------------
    // ベースアドレス
    //------------------------
    base = {
        patnam: 0,
        patgen: 0,
        patcol: 0,
        spratr: 0,
        sprpat: 0,
        sprcol: 0,
    };
    //------------------------
    // スクロール
    //------------------------
    r23     = 0;  // 表示開始ライン 上へ1ドット単位
    r25_msk = 0;
    r25_sp2 = 0;
    r26     = 0;  // 表示開始アドレス 左へ8ドット単位
    r27     = 0;  // 右へ1ドット単位
                  // 横スクロール：横512の時は2倍移動
    //------------------------
    // スプライト
    //------------------------
    spr_scan_width  = VDP.sprite_plane_width;
    spr_scan_height = VDP.sprite_plane_height;
    spr_buff_width  = VDP.sprite_plane_width;
    spr_buff_height = VDP.sprite_plane_height + 64;
    spr_buff_mag = 2;
    sprite16x16     = 0;
    sprite_double   = 0;
    //------------------------
    // お遊び
    //------------------------
    util = {
        draw_page   : 0,    // お遊び用
        x           : 0,
        y           : 0,
        color       : 15,
    }

    // ========================================================
    // コンストラクタ
    // ========================================================
 	constructor( cs ) {
        const vdp = this;

        //------------------------
        // canvas
        if (cs !== undefined) {
            if (cs.canvas !== undefined)        vdp.cs.canvas = cs.canvas;
            if (cs.pal_canvas !== undefined)    vdp.cs.pal_canvas = cs.pal_canvas;
            if (cs.page_canvas !== undefined) {
                vdp.cs.page_canvas[0] = cs.page_canvas[0];
                vdp.cs.page_canvas[1] = cs.page_canvas[1];
                vdp.cs.page_canvas[2] = cs.page_canvas[2];
                vdp.cs.page_canvas[3] = cs.page_canvas[3];
            }
            if (cs.patgen_canvas !== undefined)    vdp.cs.patgen_canvas = cs.patgen_canvas;
            if (cs.sprgen_canvas !== undefined)    vdp.cs.sprgen_canvas = cs.sprgen_canvas;
        }

        //------------------------
        // screen 情報
        vdp.screen_no = default_screen_no;
        vdp.mode_info = VDP.getScreenModeSetting( vdp.screen_no );
        vdp.width     = vdp.mode_info.width;
        vdp.height    = vdp.mode_info.height;
        vdp.max_page  = vdp.vram.length / vdp.mode_info.page_size;
        vdp.max_block = vdp.vram.length / vdp.mode_info.block_size;
        vdp.canvas_max_page = Math.min(vdp.cs.page_canvas.length, vdp.max_page);
        vdp.force_height = 0;
        vdp.auto_height = 0;
        vdp.img_width  = vdp.width;
        vdp.img_height = vdp.height;
        vdp.interlace_mode = 0;
        vdp.disp_page = 0;
        vdp.aspect_ratio = 1.177;
        vdp.base = {
            patnam: vdp.mode_info.patnam,
            patgen: vdp.mode_info.patgen,
            patcol: vdp.mode_info.patcol,
            spratr: vdp.mode_info.spratr,
            sprpat: vdp.mode_info.sprpat,
            sprcol: vdp.mode_info.sprcol,
        };

        //------------------------
        // 画面初期化
        vdp.changeScreen( vdp.screen_no , vdp.mode_info.txw, vdp.interlace_mode );
        vdp.cls();
    }

    // ========================================================
    // スクロール
    // ========================================================
    get vscroll() {
        const vdp = this;
        return vdp.r23;
    }
    set vscroll( v ) {
        const vdp = this;
        vdp.r23 = v;
    }
    get hscroll() {
        const vdp = this;
        return (vdp.r26 & 63) * 8 - (vdp.r27 & 7);
    }
    set hscroll( h ) {
        const vdp = this;
        vdp.r27 = (512-h) & 7;
        vdp.r26 = ((h + vdp.r27) >> 3) & 63;    // h / 8
    }

    // ========================================================
    // 表示ページ設定
    // ========================================================
    setPage( page ) {
        let vdp = this;
        vdp.disp_page = Math.max(0, Math.min( page, vdp.max_page - 1));
        if (vdp.screen_no < 5) {
            let page_add = vdp.disp_page * vdp.mode_info.page_size;
            let page_mask = areaMask32(vdp.mode_info.page_size);
            vdp.setPatternNameTable( (vdp.base.patnam & page_mask) + page_add );
        }
        return vdp.disp_page;
    }

    // ========================================================
    // ベースアドレス設定
    // ========================================================
    setSpriteAttributeTable( n ) {
        const vdp = this;
        if (n === undefined) {
            vdp.base.spratr = vdp.mode_info.spratr;
        } else 
        if (vdp.screen_no < 4) {
            // SPRITE mode 1
            vdp.base.spratr = n & alignMask32(0x80);
            vdp.base.sprcol = -1;
        } else {
            n &= alignMask32(0x400);
            vdp.base.spratr = n + 0x200;
            vdp.base.sprcol = n;
        }
        return vdp.base.spratr;
    }
    setSpriteAttributeTableIdx( n ) {
        const vdp = this;
        if (n === undefined) {
            vdp.base.spratr = vdp.mode_info.spratr;
        } else 
        if (vdp.screen_no < 4) {
            // SPRITE mode 1
            vdp.base.spratr = n * 0x80;
            vdp.base.sprcol = -1;
        } else {
            vdp.base.spratr = n * 0x400 + 0x200;
            vdp.base.sprcol = n * 0x400;
        }
        return vdp.base.spratr;
    }
    setSpritePatternTable( n ) {
        const vdp = this;
        if (n === undefined) {
            vdp.base.sprpat = vdp.mode_info.sprpat;
        } else {
            vdp.base.sprpat = n & alignMask32(0x800);
        }
        return vdp.base.sprpat;
    }
    setSpritePatternTableIdx( n ) {
        const vdp = this;
        if (n === undefined) {
            vdp.base.sprpat = vdp.mode_info.sprpat;
        } else {
            vdp.base.sprpat = n * 0x800;
        }
        return vdp.base.sprpat;
    }
    setPatternNameTable( n ) {
        const vdp = this;
        if (n === undefined) {
            vdp.base.patnam = vdp.mode_info.patnam;
        } else {
            vdp.base.patnam = n & alignMask32(vdp.mode_info.u_patnam);
        }
        if (vdp.screen_no < 5) {
            vdp.disp_page = Math.floor(vdp.base.patnam / vdp.mode_info.page_size);
        }
        return vdp.base.patnam;
    }
    setPatternNameTableIdx( n ) {
        const vdp = this;
        if (n === undefined) {
            vdp.base.patnam = vdp.mode_info.patnam;
        } else {
            vdp.base.patnam = vdp.mode_info.u_patnam * n;
        }
        return vdp.base.patnam;
    }
    setPatternGeneratorTable( n ) {
        const vdp = this;
        if (n === undefined) {
            vdp.base.patgen = vdp.mode_info.patgen;
        } else {
            vdp.base.patgen = n & alignMask32(vdp.mode_info.u_patgen);
        }
        return vdp.base.patgen;
    }
    setPatternGeneratorTableIdx( n ) {
        const vdp = this;
        if (n === undefined) {
            vdp.base.patgen = vdp.mode_info.patgen;
        } else {
            vdp.base.patgen = vdp.mode_info.u_patgen * n;
        }
        return vdp.base.patgen;
    }
    setPatternColorTable( n ) {
        const vdp = this;
        if (n === undefined) {
            vdp.base.patcol = vdp.mode_info.patcol;
        } else {
            vdp.base.patcol = n & alignMask32(vdp.mode_info.u_patgen);
        }
        return vdp.base.patcol;
    }
    setPatternColorTableIdx( n ) {
        const vdp = this;
        if (n === undefined) {
            vdp.base.patcol = vdp.mode_info.patcol;
        } else {
            vdp.base.patcol = vdp.mode_info.u_patgen * n;
        }
        return vdp.base.patcol;
    }

    // ========================================================
    // カラーパレット初期化
    // ========================================================
    resetPalette() { 
        this.palette.setPalette( this.pal_def.color ); 
    }
    // ========================================================
    // カラーパレットを設定
    // ========================================================
    restorePalette( d ) {
        const vdp = this;
        if (d === undefined) {
            // VRAMから読み込む
            vdp.palette.setPalette( vdp.vram.subarray( vdp.mode_info.paltbl, vdp.mode_info.paltbl + 32  ) );
        } else {
            // 指定データから読み込む
            vdp.palette.setPalette( d );
        }
    }
    // ========================================================
    // カラーパレットを返す
    // ========================================================
    getPalTbl() {
        return this.palette.getPalTbl();
    }

    // ========================================================
    // デフォルトカラーパレット更新
    // ========================================================
    updateDefaultColorPalette() {
        const vdp = this;
        if ((vdp.screen_no < 4) && (pal_use_tms9918)) {
            vdp.pal_def = new Palette( VDP.palette_count, VDP.msx1fpal );
            vdp.pal_def.setRgba( VDP.tms9918pal8888 ); // 8888精度の色で表示
        } else {
            vdp.pal_def = new Palette( VDP.palette_count, VDP.msx2pal );
        }
    }

    // ========================================================
    // 画面モード変更
    // ========================================================
    changeScreen( screen_no, txw, interlace_mode, force_height, reset_base ) {
        const vdp = this;

        let old_screen_no = vdp.screen_no;
        let old_interlace_mode = vdp.interlace_mode;

        let mode_info = VDP.getScreenModeSetting( screen_no, txw );
        vdp.interleaveVram( mode_info.page_size );
        vdp.mode_info = mode_info;
        vdp.screen_no = screen_no;
        vdp.width  = vdp.mode_info.width;
        vdp.height = vdp.mode_info.height;
        vdp.max_block  = vdp.vram.length / vdp.mode_info.block_size;
        vdp.max_page  = vdp.vram.length / vdp.mode_info.page_size;
        vdp.canvas_max_page = Math.min(vdp.cs.page_canvas.length, vdp.max_page);

        vdp.updateDefaultColorPalette();

        vdp.r23 = 0;
        vdp.r25_msk = 0;
        vdp.r25_sp2 = 0;
        vdp.r26 = 0;
        vdp.r27 = 0;

        nouse_patgen = false;
        nouse_patcol = false;

        if (vdp.auto_height) {
            vdp.height = vdp.auto_height;
        }
        if (force_height === undefined) {
            force_height = vdp.force_height;
        }
        if (force_height) {
            vdp.height = force_height;
        }

        if (screen_no != old_screen_no) {
            if (5 <= vdp.screen_no) {
                vdp.setPage( 0 );
            }
        }
        if (interlace_mode === undefined ) {
            if (screen_no != old_screen_no) {
                interlace_mode = 0;
            } else {
                interlace_mode = vdp.interlace_mode;
            }
        }
        vdp.setInterlaceMode( interlace_mode );

        vdp.img_width  = vdp.width * (vdp.width <= 256 ? 2 : 1); // 常にNTSCラインサイズ
        vdp.img_height = VDP.scan_line_count * 2; // 常にNTSCラインフルサイズ

        // base address
        reset_base |= false;
        if (reset_base || (screen_no != old_screen_no)) {
            vdp.base.patnam = vdp.mode_info.patnam;
            vdp.base.patgen = vdp.mode_info.patgen;
            vdp.base.patcol = vdp.mode_info.patcol;
            vdp.base.spratr = vdp.mode_info.spratr;
            vdp.base.sprpat = vdp.mode_info.sprpat;
            vdp.base.sprcol = vdp.mode_info.sprcol;
        }

        if (vdp.cs.canvas) {
    		vdp.initCanvas();
        }

        updateBaseAddressList();
    }
    setInterlaceMode( interlace_mode ) {
        const vdp = this;
        const old_interlace_mode = vdp.interlace_mode;
        if (vdp.screen_no < 5) {
            // SCREEN0～4は仕様が分からないのでインターレースモードは禁止
            vdp.interlace_mode = 0;
        } else {
            vdp.interlace_mode = interlace_mode;
            if (old_interlace_mode != vdp.interlace_mode) {
                // ページはインターレース（＋フリップ）時では奇数に指定
                vdp.setPage( (vdp.disp_page & ~1) | vdp.interlace_mode | vdp.r25_sp2 );
            }
        }
}

    // ========================================================
    // 描画キャンバス初期化
    // ========================================================
    initCanvas( cs ) {
    	const vdp = this;

        if (cs !== undefined) {
            if (cs.canvas !== undefined)        vdp.cs.canvas = cs.canvas;
            if (cs.pal_canvas !== undefined)    vdp.cs.pal_canvas = cs.pal_canvas;
            if (cs.page_canvas !== undefined) {
                vdp.cs.page_canvas[0] = cs.page_canvas[0];
                vdp.cs.page_canvas[1] = cs.page_canvas[1];
                vdp.cs.page_canvas[2] = cs.page_canvas[2];
                vdp.cs.page_canvas[3] = cs.page_canvas[3];
            }
            if (cs.patgen_canvas !== undefined)    vdp.cs.patgen_canvas = cs.patgen_canvas;
            if (cs.sprgen_canvas !== undefined)    vdp.cs.sprgen_canvas = cs.sprgen_canvas;
        }

        if (!vdp.cs.canvas) {
            console.log('initCanvas - vdp.cs.canvas is null.');
            return;
        }

         // イメージバッファ作成
         vdp.offscreen[0] = new OffscreenCanvas(vdp.img_width, vdp.img_height); //最終出力先
         vdp.offscreen[1] = new OffscreenCanvas(vdp.width, VDP.scan_line_count * vdp.canvas_max_page); // ページ分
         vdp.offscreen[2] = new OffscreenCanvas(vdp.spr_buff_mag * vdp.spr_buff_width,
                                                vdp.spr_buff_mag * vdp.spr_buff_height); // 1画面 + パターンリスト
        var ctx = vdp.offscreen[1].getContext('2d');
        vdp.imgData = ctx.createImageData(vdp.offscreen[1].width, vdp.offscreen[1].height);
        vdp.sprData = ctx.createImageData(vdp.spr_buff_width, this.spr_buff_height);
    }
    // ========================================================
    // VRAM配列変更
    // ========================================================
    interleaveVram( dst_page_size ) {
        const vdp = this;
        if (!vram_interleave || !vdp.mode_info
         || (dst_page_size == vdp.mode_info.page_size)) {
            return;
        }

        let length = vdp.vram.length >> 1;
        let vram = new Uint8Array( vdp.vram.length );
        let src = vdp.vram;

        if (dst_page_size == 0x10000) {
            // page 0x8000 mode -> page 0x10000 mode
            let p = 0;
            let p1 = 0x10000;
            for (let p0 = 0; p0 < length;) {
                vram[p++] = src[p0++];
                vram[p++] = src[p1++];
            }
        } else {
            // page 0x10000 mode -> page 0x8000 mode
            let p = 0;
            let p1 = 0x10000;
            for (let p0 = 0; p0 < length;) {
                vram[p0++] = src[p++];
                vram[p1++] = src[p++];
            }
        }
        vdp.vram = vram;
    }

    // ========================================================
    // VRAMクリア
    // ========================================================
    cls( resetPalette ) {
        const vdp = this;

        vdp.vram.fill( 0 );
        if (resetPalette === undefined) resetPalette = false;
        if (!pal_not_use_vram || resetPalette) {
            vdp.resetPalette();
            vdp.vram.set( vdp.getPalTbl(), vdp.mode_info.paltbl );
        }

        // お遊び
        vdp.util.x = 0;
        vdp.util.y = 0;
        vdp.util.color = 15;

        // 初期値
        const b = vdp.vram;
        const tx_size = vdp.mode_info.txw * vdp.mode_info.txh;
        let n = vdp.base.patnam;
        switch (vdp.screen_no) {
        case 0:
        case 1:
            b.fill(32,vdp.base.patnam, vdp.base.patnam + tx_size);
            b.fill(0xf0, vdp.base.patcol, vdp.base.patcol + 32);
            b.set( fontdat, vdp.base.patgen );
            /*
            // test
            if (-1 < vdp.base.patcol) {
                for (var i=0; i<32; ++i) {
                    b[vdp.base.patcol + i] = i;
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
            b.fill(0xf0, vdp.base.patcol, vdp.base.patcol + tx_size * 8);
            /*
            // test
            for (var i=0; i<tx_size * 8; ++i) {
                b[vdp.base.patcol + i] = i;
            }
            */
            break;
        case 3:
            for (let i = 0; i < tx_size; ++i, ++n) {
                b[n] = (i & 31) + ((i >> 2) & 0xffe0);
            }
            /*
            // test
            for (var i=0; i<tx_size * 8; ++i) {
                b[vdp.base.patgen + i] = i;
            }
            //*/
            break;
        }
    }

    // ========================================================
    // バイナリ転送
    // ========================================================
    loadBinary( d, offset )
    {
    	const vdp = this;
        if (offset == undefined) {
            offset = vdp.util.draw_page * vdp.mode_info.namsiz;
        }
        let limit = vdp.vram.length - offset;
        if (offset > limit) {
            return;
        }
        if (d.length > limit) {
            vdp.vram.set( d.subarray(0, limit), offset );
        } else {
            vdp.vram.set( d, offset );
        }
    }

    // ========================================================
    // メインキャンバスのHTML表示サイズを設定
    // ========================================================
    setCanvasSize()
    {
    	const vdp = this;
        if (vdp.cs.canvas) {
            // メインキャンバスサイズ
            vdp.cs.canvas.height = vdp.height * 2;
            if (vdp.width <= 256) {
                vdp.cs.canvas.width = vdp.width * 2 * vdp.aspect_ratio;
            } else {
                vdp.cs.canvas.width = vdp.width * vdp.aspect_ratio;
            }
        }
    }

    // ========================================================
    // 描画出力
    // ========================================================
    draw( disp_mode ) {
    	const vdp = this;

        const screen_no = vdp.screen_no;
        const scan_line_count = VDP.scan_line_count;
        const disp_page = (screen_no < 5) ? (vdp.disp_page & 1) : vdp.disp_page;

        //------------------------
        // メインキャンバス
        //------------------------
        if (vdp.cs.canvas) {
            vdp.setCanvasSize();

            var ctx = vdp.cs.canvas.getContext('2d');
            ctx.imageSmoothingEnabled = false;//canvas_smoothing.checked;

            let vscroll = vdp.vscroll;
            if (vscroll) {
                if (screen_no == 0) {
                    for (let i = 0; i < vdp.height; ++i) {
                        let y = (((i & 0xfff8) + ((vscroll + i) & 7) ) & 255) * 2;
                        ctx.drawImage( vdp.offscreen[0],
                            0, y    , vdp.img_width, 2,
                            0, i * 2, vdp.cs.canvas.width, 2 );
                    }
                } else {
                    for (let i = 0; i < vdp.height; ++i) {
                        let y = ((i + vscroll) & 255) * 2;
                        ctx.drawImage( vdp.offscreen[0],
                            0, y    , vdp.img_width, 2,
                            0, i * 2, vdp.cs.canvas.width, 2 );
                    }
                }
            } else {
                ctx.drawImage( vdp.offscreen[0],
                    0, 0, vdp.img_width, vdp.height * 2,
                    0, 0, vdp.cs.canvas.width, vdp.cs.canvas.height );
            }
        }

        //------------------------
        // ページ毎表示キャンバス
        //------------------------
        if (vdp.cs.page_canvas) {
            var offscreen = vdp.offscreen[1];

            let height = vdp.height;

            let y = 0;
            if (screen_no < 5) {
                if (!vdp.r25_sp2 || !screen_no) {
                    y = scan_line_count * disp_page;
                }
            }
            for (var pg = 0; pg < vdp.cs.page_canvas.length; ++pg) {
                if (pg >= vdp.canvas_max_page) break;

                var canvas = vdp.cs.page_canvas[pg];
                if ((pg == 2) && (screen_no < 5)) {
                    canvas = vdp.cs.patgen_canvas;
                    y = scan_line_count * 2;
                    //if (3 == screen_no) {
                    //    height = 256; // chara_height * chara_count * 4 / txw;
                    //} else
                    if (1 < screen_no) {
                        height = 64 * 3; // chara_height * chara_count * chara_gen_count / txw;
                    } else {
                        height = 64;    // chara_height * chara_count  / txw;
                    }
                }
                if (canvas) {
                    canvas.width  = vdp.cs.canvas.width;
                    canvas.height = height * 2;
                    ctx = canvas.getContext('2d');
                    ctx.imageSmoothingEnabled = false;//canvas_smoothing.checked;
                    ctx.drawImage( offscreen, 
                        0, y, vdp.width, height,
                        0, 0, canvas.width, canvas.height );
                }
                y += scan_line_count;
            }
        }
        //------------------------
        // スプライトジェネレータ
        //------------------------
        if (vdp.cs.sprgen_canvas) {
            var offscreen = vdp.offscreen[2];

            let mag = vdp.spr_buff_mag;
            let h = 0;  // vdp.spr_scan_height
            let lh = vdp.spr_buff_height - h;

            let canvas = vdp.cs.sprgen_canvas;
            canvas.width  = vdp.cs.canvas.width;
            canvas.height = lh * 2;
            ctx = canvas.getContext('2d');
            ctx.imageSmoothingEnabled = false;//canvas_smoothing.checked;
            ctx.drawImage( offscreen, 
                0, h * mag, offscreen.width, lh * mag,
                0, 0, canvas.width, canvas.height );
        }

        //------------------------
        // パレットキャンバス
        //------------------------
        if (vdp.cs.pal_canvas)
        {
            var palette = vdp.palette;
            if (!palette_use) {
                palette = vdp.pal_def;
            }
            if (screen_no == 8) {
                palette = vdp.pal256;
            }
            var pal = palette.rgba;
            if (use_grayscale ^ use_grayscale_tmp) {
                pal = palette.gray;
            }
            //if (nouse_patcol) pal = palette.gray;

            var canvas = vdp.cs.pal_canvas;
            var ctx = canvas.getContext('2d');

            canvas.width = 32 * VDP.palette_count;
            canvas.height = 24;

            ctx.fillStyle = "black";
            ctx.fillRect(0,0,canvas.width,canvas.height);

            var w = Math.floor(canvas.width / pal.length);
            for (var i = 0; i < pal.length; ++i) {
                ctx.fillStyle = rgb_string(pal[i]);
                ctx.fillRect(
                    canvas.width * i / pal.length, 0,
                    w, canvas.height);
            }
        }
    }
    // ========================================================
    // 描画内部更新
    // ========================================================
    update() {
    	const vdp = this;

        if (!vdp.imgData) {
            console.log('const - this.imgData is null.');
            return;
        }

        // ========================================================
        // ラスタライズ
        // ========================================================
        switch (vdp.screen_no) {
        case 0:
            vdp.update_chrgen(0xff, 6, -1);
            break;
        case 1:
            vdp.update_chrgen(0xff, 8, 6);
            break;
        case 2:
        case 4:
            vdp.update_chrgen(0x3ff, 8, 0);
            break;
        case 3:
            vdp.update_multi_color();
            break;
        case 5:
        case 7:
            vdp.update_bitmap16();
            break;
        case 6:
        case 9:
            vdp.update_bitmap4();
            break;
        case 8:
            vdp.update_bitmap256();
            break;
        case 10:
        case 11:
            vdp.update_bitmap_yae();
            break;
        case 12:
            vdp.update_bitmap_yjk();
            break;
        }
        if (-1 < vdp.base.spratr) {
            let mode2 = (vdp.screen_no < 4) ? 0 : 1;
            vdp.update_spr( mode2, vdp.sprite16x16, vdp.sprite_double, 0 );
        }

        vdp.pre_render();
    }
    // ========================================================
    // 描画事前処理
    // ========================================================
    pre_render() {
    	const vdp = this;

        if (!vdp.imgData) {
            console.log('const - this.imgData is null.');
            return;
        }

        // ========================================================
        // Pre-Render
        // ========================================================
        const screen_no = vdp.screen_no;
        let disp_page = (screen_no < 5) ? (vdp.disp_page & 1) : vdp.disp_page;
        let disp_page2 = disp_page;

        //--------------------------------
        // ページワークスクリーンにピクセルイメージを反映
        //--------------------------------
        let work = vdp.offscreen[1];
        var ctx = work.getContext('2d');
        ctx.putImageData( vdp.imgData, 0, 0 );

        //--------------------------------
        // メインワークスクリーンからメインスクリーンにコピー
        //--------------------------------
        const scan_line_count = VDP.scan_line_count;
        let main = vdp.offscreen[0];
        ctx = main.getContext('2d');
        ctx.imageSmoothingEnabled = false;//canvas_smoothing.checked;

        //--------------------------------
        // 横スクロール 計算
        let hofs = vdp.r27 * main.width / 256;
        let sofs = 0;
        let hofs2 = 0;
        let hwid2 = 0;
        if (screen_no) {
            let ofs = (vdp.r26 * 8) & 255;
            let ofs2 = (255 - ofs) & 255;
                sofs = ofs * work.width / 256;
            hofs2 = ofs2 * main.width / 256 + hofs;
            hwid2 = ofs * main.width / 256;
        }
        if (vdp.r25_sp2 && screen_no) {
            if (31 < vdp.r26) {
                disp_page2 &= 2;
            } else {
                disp_page &= 2;
            }
        }
        //--------------------------------

        //--------------------------------
        // インターレース＆縦スクロール
        //--------------------------------
        if (vdp.interlace_mode && (5 <= screen_no)) {
            // 奇数行・偶数行を交互に合成
            let y = 0;
            let l0  = (disp_page  & 2 ) * scan_line_count;
            let l1  = (disp_page      ) * scan_line_count;
            let l10 = (disp_page2 & 2 ) * scan_line_count;
            let l11 = (disp_page2     ) * scan_line_count;
            for (var i = 0; i < scan_line_count;  ++i, y+=2) {
                ctx.drawImage( work, sofs, i + l0, work.width, 1, hofs, y    , main.width, 1 );
                ctx.drawImage( work, sofs, i + l1, work.width, 1, hofs, y + 1, main.width, 1 );
                if (sofs) {
                    ctx.drawImage( work, 0, i + l10, sofs, 1, hofs2, y    , hwid2, 1 );
                    ctx.drawImage( work, 0, i + l11, sofs, 1, hofs2, y + 1, hwid2, 1 );
                }
            }
        } else {
            // 表示ページ部分をそのまま転送
            let y  = disp_page  * scan_line_count;
            let y2 = disp_page2 * scan_line_count;
            ctx.drawImage( work,
                 sofs, y, work.width, scan_line_count,
                 hofs, 0, main.width, scan_line_count * 2 );
            if (sofs) {
                ctx.drawImage( work,
                    0    , y2, sofs , scan_line_count,
                    hofs2, 0 , hwid2, scan_line_count * 2 );
            }
        }

        //--------------------------------
        // 横スクロール マスク
        //--------------------------------
        if (vdp.r25_msk) {
            ctx.fillStyle = 'rgb(0,0,0)';
            ctx.fillRect(0,0, 8 * main.width / 256, main.height);
        } else
        if (hofs) {
            ctx.fillStyle = 'rgb(0,0,0)';
            ctx.fillRect(0,0, hofs, main.height);
        }

        //--------------------------------
        // スプライト 合成
        //--------------------------------
        if (-1 < vdp.base.spratr) {
            //--------------------------------
            // ワークスクリーン（２ページ分）にピクセルイメージを反映
            //--------------------------------
            let dst = vdp.offscreen[2];
            var ctx = dst.getContext('2d');
            //ctx.putImageData( vdp.sprData, 0, 0 );
            vdp.spriteBlendToScreen( true, dst, sprite_limit_mode, 0.5 );
            //--------------------------------
            // メインスクリーンに合成
            //--------------------------------
            if (!vdp.sprite_disable) {
                vdp.spriteBlendToScreen( false, vdp.offscreen[0], sprite_limit_mode, 0.5 );
            }
        }
    }
    // ========================================================
    // スプライト オフスクリーン → 表示用スクリーン
    // ========================================================
    spriteBlendToScreen( direct, dst, blend_type, mag, dx, dy, dw, dh )
    {
        const vdp = this;

        let sd = vdp.sprData;

        const alpha_spec = 142;//direct ? 128 : 128;

        if (dx === undefined) dx = 0;
        if (dy === undefined) dy = 0;
        if (dw === undefined) dw = dst.width;
        if (dh === undefined) dh = dst.height;

        let ctx = dst.getContext('2d', {willReadFrequently: true});
        ctx.imageSmoothingEnabled = false;//canvas_smoothing.checked;
        let dd = ctx.getImageData( dx, dy, dw, dh );
        if ((direct !== undefined) && direct) {
            dd.data.fill(0);
        }

        let ddd = dd.data;
        let sdd = sd.data;

        // アルファブレンド＆拡大
        let xmag = mag;//sd.width / dd.width;
        let ymag = mag;
        let src_line_size = sd.width << 2;
        let dst_line_size = dd.width << 2;
        for (let y = 0; y < dd.height; ++y) {
            for (let x = 0; x < dd.width; ++x) {
                let srcx = Math.floor(x * xmag);
                let srcy = Math.floor(y * ymag);
                let si = (srcx << 2) + srcy * src_line_size;
                //let sa = sd.data.subarray(si, si + 4);
                let a = sdd[si + 3];
                if (0 < a) {
                    let di = (x << 2) + y * dst_line_size;
                    //let da = dd.data.subarray(di, di + 4);
                    if ((a == 255)
                     || (blend_type == 1) // 制限なし
                     || ((blend_type == 3) && !((y ^ x) & 1)) // 網掛け
                    ) {
                        ddd[di + 0] = sdd[si + 0];
                        ddd[di + 1] = sdd[si + 1];
                        ddd[di + 2] = sdd[si + 2];
                        ddd[di + 3] = 255;
                    } else 
                    if (blend_type == 2) { // 半透明
                        if (!ddd[di + 3]) {
                            ddd[di + 0] = sdd[si + 0];
                            ddd[di + 1] = sdd[si + 1];
                            ddd[di + 2] = sdd[si + 2];
                            ddd[di + 3] = 128;
                        } else {
                            if (128 == alpha_spec) {
                                a = alpha_spec;
                                let b = 255 - a;
                                ddd[di + 0] = ( ddd[di + 0] * b + sdd[si + 0] * a ) / 255;
                                ddd[di + 1] = ( ddd[di + 1] * b + sdd[si + 1] * a ) / 255;
                                ddd[di + 2] = ( ddd[di + 2] * b + sdd[si + 2] * a ) / 255;
                            } else {
                                // 50%
                                ddd[di + 0] = ( ddd[di + 0] + sdd[si + 0] ) / 2;
                                ddd[di + 1] = ( ddd[di + 1] + sdd[si + 1] ) / 2;
                                ddd[di + 2] = ( ddd[di + 2] + sdd[si + 2] ) / 2;
                            }
                        }
                    }
                }
            }
        }
        ctx.putImageData( dd, dx, dy );
    }

    // ========================================================
    // スプライト プレーン処理
    // 表示制限ありのラスタライザ（ライン単位処理）
    // ========================================================
    update_spr( mode2, x16, x2, tp ) 
    {
    	const vdp = this;
        // tp はカラーコード0を透明ではなくパレットからーで表示
        tp &= mode2; // mode 2でのみ有効

        if (!vdp.sprData) {
            console.log('update_spr - this.sprData is null.');
            return;
        }
        var pal = vdp.palette;
        if (!palette_use) {
            pal = vdp.pal_def;
        }
        if (vdp.screen_no == 8) {
            pal = vdp.pal8spr;
        }
        var rgba = pal.rgba;
        if (use_grayscale ^ use_grayscale_tmp) {
            rgba = pal.gray; 
        }

        const pg_count = 2;
        let chr_count = 1 + x16 * 3;

        const bit_masks = [
            [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01],
            [0x80, 0x80, 0x40, 0x40, 0x20, 0x20, 0x10, 0x10,
             0x08, 0x08, 0x04, 0x04, 0x02, 0x02, 0x01, 0x01],
        ];

        let chr_shift = x2;
        let bit_mask = bit_masks[chr_shift];
        let chrw = 8 << chr_shift;
        let sprh = (8 + 8 * x16) << chr_shift;

        let buf = vdp.sprData.data;
        let d = vdp.vram;

        const stop_y = mode2 ? 216 : 208; // 以降非表示
        const pat_count = 256;
        const width = vdp.spr_scan_width;
        const height = vdp.spr_scan_width; 
        const dotw = 4; // rgba
        const line_size = dotw * width;

        const sprpat = vdp.base.sprpat;
        const sprcol = vdp.base.sprcol;  // mode1 : no use
        const spratr = vdp.base.spratr;

        let atr_y   = stop_y - 1;
        let atr_x   = 0;
        let atr_pat = 0;
        let atr_col = 0;
        const atr_size = 4;

        const EC_bit = 0x80;    // 左に32ドットずらす
        const CC_bit = 0x40;    // 若くて最も近い番号のスプライトと色をOR

        let dotcol = 15; // color
        let pgofs = 0;
        let chr_step = 1;

        const line_limit = 4 + 4 * mode2;
        const no_limit = sprite_limit_mode;
        const ar_alpha = [0, 255, 128, 128]; //
        let alpha = 255;

        let line_buff_i = new Uint8Array(width);
        let line_buff_c = new Uint8Array(width);
        buf.fill(0);

        let write0bit = 0; // 透明ビットを描画する

        let spr_count = 32;
        let use_sprcol = mode2;
        let pg, y, i, n, cx, iy, idy, ix, x, idx;
        let line_counter= 0, line_counter_d = 1;
        let cur_line_cc0, cc;
        let ec_shift, ofx;
        let pa, pattern, col, c;

        for (pg = 0; pg < pg_count; ++pg) {

            for (y = 0; y < vdp.spr_scan_height; ++y) {
                line_counter = 0;
                line_buff_i.fill(0);
                line_buff_c.fill(0);
                cur_line_cc0 = spr_count;
                alpha = 255;
                for (i = 0; i < spr_count; i+=chr_step) {
                    // 1ラインの表示上限を越えた場合
                    if (line_counter >= line_limit) {
                        if (0 == no_limit) break; // 非表示
                        alpha = ar_alpha[no_limit];
                    }

                    if (!pg) {
                        // ATRテーブル
                        n = spratr + i * atr_size;
                        atr_y   = d[n + 0];
                        atr_x   = d[n + 1];
                        atr_pat = d[n + 2];
                        atr_col = d[n + 3];
                        if (atr_y == stop_y) break;
                        if (x16) atr_pat &= 0xfc;
                    } else {
                        // パターン一覧
                        if (x16) {
                            atr_y   = ((i >> 6) * 16) & 255;
                            atr_x   = (i << 2) & 255;
                        } else {
                            atr_y   = ((i >> 5) * 8) & 255;
                            atr_x   = (i << 3) & 255;
                        }
                        atr_pat = i;
                        atr_col = 15;
                    }

                    // ラインにヒットするか
                    iy = (y - atr_y - 1) & 255; // 表示Y座標
                    if (sprh <= iy) continue;

                    //--------------------------------
                    // ライン上に存在

                    // パターン＆カラーの参照位置補正
                    idy = iy >> chr_shift;

                    // スプライトカラーテーブル
                    if (use_sprcol) {
                        atr_col = d[sprcol + idy + (i << 4)];
                    }
                    cc = use_sprcol && (atr_col & CC_bit);
                    ec_shift = (atr_col & EC_bit) >> 2;
                    
                    if (cc) {
                        if (i < cur_line_cc0) {
                            line_counter += line_counter_d; //カウントはする
                            continue; // CC0が存在しない
                        }
                    } else {
                    // このラインに存在するCC=0の最新番号
                        cur_line_cc0 = i;
                    }

                    // TP=0 なら カラー0は透過
                    if (!tp && !(atr_col & 15))
                    {
                        line_counter += line_counter_d; //カウントはする
                        continue;
                    }

                    // 表示
                    pa = sprpat + atr_pat * 8 + idy;
                    ofx = 0;
                    for (cx = 0; cx <= x16; ++cx) {
                        pattern = d[pa];
                        for (ix = 0; ix < chrw; ++ix) {
                            x = atr_x + ix + ofx;
                            x -= ec_shift;  // EC bit => 32
                            if (x < 0) continue;
                            if (255 < x) continue;
                            idx = x * dotw + ((y & 255) + pgofs) * line_size;
                            if (pattern & bit_mask[ix]) {
                                if ((!buf[ idx + 3 ])
                                 || (cc && (line_buff_i[x] == cur_line_cc0)) // CC=1のとき、直近のCC=0のピクセルならOK
                                ) {
                                    col = atr_col;
                                    if (cc) {
                                        col |= line_buff_c[x]; // OR 合成
                                    } else {
                                        line_buff_i[x] = i;
                                    }
                                    col &= 15;
                                    line_buff_c[x] = col;
                                    c = rgba[ col ];
                                    buf[ idx + 0 ] = c[0];
                                    buf[ idx + 1 ] = c[1];
                                    buf[ idx + 2 ] = c[2];
                                    buf[ idx + 3 ] |= alpha;
                                }
                            } else
                            if (write0bit) {
                                buf[ idx + 0 ] = 0;
                                buf[ idx + 1 ] = 0;
                                buf[ idx + 2 ] = 0;
                                buf[ idx + 3 ] = 255;
                            }
                        }
                        pa += 16; 
                        ofx += chrw;
                    }
                    //
                    line_counter += line_counter_d;
                }
            }
            // パターン一覧
            pgofs += 256;
            pal = vdp.pal_bf;
            chr_step = chr_count;
            write0bit = 1;
            spr_count = pat_count;
            use_sprcol = 0;
            line_counter_d = 0;

            chr_shift = 0;
            bit_mask = bit_masks[chr_shift];
            chrw = 8 << chr_shift;
            sprh = (8 + 8 * x16) << chr_shift;
        }
    }
    // ========================================================
    // PCG プレーン処理
    // ========================================================
    update_chrgen( chr_mask, chr_w, coltbl_shift ) {
    	const vdp = this;

        const bit_shift = [7, 6, 5, 4, 3, 2, 1, 0];

        if (!vdp.imgData) {
            console.log('update_chrgen - this.imgData is null.');
            return;
        }

        var pal = vdp.palette;
        if (!palette_use) {
            pal = vdp.pal_def;
        }
        var rgba = pal.rgba;
        if (use_grayscale ^ use_grayscale_tmp) {
            rgba = pal.gray; 
        }

        // SC6以下は1ページ0x8000
        //const pg_count = Math.min( Math.floor(vdp.vram.length / 0x8000), vdp.cs.page_canvas.length);
        const pg_count = 2 + 1; // 2ページ + キャラジェネ
        const last_pg = pg_count - 1;
        const page_size = vdp.mode_info.page_size;
        const page_mask = 0xffffffff ^ page_size;

        let buf = vdp.imgData.data;
        let d = vdp.vram;
        let cd = vdp.vram;

        let patnam = vdp.base.patnam & page_mask;
        const patgen = vdp.base.patgen;
        let patcol = vdp.base.patcol;
        let txw = Math.floor((vdp.width  + chr_w - 1) / chr_w);
        let txh = (VDP.scan_line_count + 7) >> 3;  // / 8
        const line_size = 4 * vdp.width;
        let chr_size = 4 * chr_w;

        let colset = [0, 15];

        let odx = 0, ody, dy, dx;
        let pg, i, x, y, px, py;
        let chr_d, pattern, col;
        let cid, c;

        let ndx = patnam;
        for (pg = 0; pg < pg_count; ++pg) {
            if (pg == last_pg) {
                // chara pattern generator preview
                txw = 32;
                if (vdp.screen_no < 2) {
                    txh = 8;
                }
            }
            i = 0;
            for (y = 0; y < txh; ++y) {
                ody = odx;
                for (x = 0; x < txw; ++x) {
                    // chr gen view : page 1
                    if (pg == last_pg) {
                        chr_d = i;
                    } else {
                        chr_d = (d[ndx++] + (i & 0xff00));
                    }
                    chr_d &= chr_mask;  // screen 1 / 2,4
                    chr_d <<= 3;
                    dy = ody;
                    for(py = 0; py < 8; ++py, ++chr_d) {
                        if (nouse_patgen) {
                            pattern = 0xaa;
                        } else {
                            pattern = d[patgen + chr_d];
                        }
                        if ((0 <= coltbl_shift) && (0 <= patcol)) {
                            if (nouse_patcol) {
                                colset[0] = 0;
                                colset[1] = 15;
                            } else {
                                col = cd[patcol + (chr_d >> coltbl_shift)];
                                colset[0] = col & 15;
                                colset[1] = col >> 4;
                            }
                        }
                        dx = dy; 
                        for(px = 0; px < chr_w; ++px) {
                            cid = (pattern >> bit_shift[px]) & 1;
                            c = rgba[ colset[cid] ];
                            buf[ dx + 0 ] = c[0];
                            buf[ dx + 1 ] = c[1];
                            buf[ dx + 2 ] = c[2];
                            buf[ dx + 3 ] = c[3];
                            dx+=4;
                        }
                        dy += line_size;
                    }
                    ody += chr_size;
                    ++i;
                }
                odx += line_size << 3;
            }
            patnam += page_size;
            ndx = patnam; 
        }
    }
    // ========================================================
    // MULTI COLOR プレーン処理
    // ========================================================
    update_multi_color() {
    	const vdp = this;

        if (!vdp.imgData) {
            console.log('update_multi_color - this.imgData is null.');
            return;
        }
        let pal = vdp.palette;
        if (!palette_use) {
            pal = vdp.pal_def;
        }
        var rgba = pal.rgba;
        if (use_grayscale ^ use_grayscale_tmp) {
            rgba = pal.gray; 
        }
        //const pg_count = Math.min( Math.floor(vdp.vram.length / 0x8000), vdp.cs.page_canvas.length);
        const pg_count = 2 + 1; // 2ページ + キャラジェネ
        const last_pg = pg_count - 1;
        const page_size = vdp.mode_info.page_size;
        const page_mask = 0xffffffff ^ page_size;

        let buf = vdp.imgData.data;
        let d = vdp.vram;

        let patnam = vdp.base.patnam & page_mask;
        const patgen = vdp.base.patgen;
        const txw = (vdp.width  + 7) >> 3; // / 8;
        let   txh = (VDP.scan_line_count + 7) >> 3; // / 8;
        //const tx_size = txw * txh;
        const line_size = 4 * vdp.width;
        const b_line_size = line_size * 4; // 1block 4x4px

        const c_shift = [4, 0];
        let odx = 0, dx, dy, ddy, ddx;
        let chr, colval;
        let pg, y, x, iy, diy, i, c, dix;

        for (pg = 0; pg < pg_count; ++pg) {
            if (pg == last_pg) {
                //txh = 32;
            }
            for (y = 0; y < txh; ++y) {
                dx = odx;
                for (x = 0; x < txw; ++x) {
                    if (pg == last_pg) {
                        chr = x + (y >> 2) * txw;
                    } else {
                        chr = d[patnam + x + y * txw];
                    }
                    dy = dx;
                    for (iy = 0; iy < 2; ++iy) {
                        colval = d[ patgen + (chr * 8) + (y & 3) * 2 + iy ];
                        // 8x4
                        ddy = dy;
                        for (diy = 0; diy < 4; ++diy) {
                            // 8x1
                            ddx = ddy;
                            for(i = 0; i < 2; ++i) {
                                c = rgba[ (colval >> c_shift[i]) & 15 ];
                                // 4x1
                                for (dix = 0; dix < 4; ++dix) {
                                    buf[ ddx + 0 ] = c[0];
                                    buf[ ddx + 1 ] = c[1];
                                    buf[ ddx + 2 ] = c[2];
                                    buf[ ddx + 3 ] = c[3];
                                    ddx += 4;
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
            patnam += page_size;
        }
    }
    // ========================================================
    // 4bitカラービットマップ プレーン処理
    // ========================================================
    update_bitmap16() {
    	const vdp = this;
        if (!vdp.imgData) {
            console.log('update_bitmap16 - this.imgData is null.');
            return;
        }
        let pal = vdp.palette;
        if (!palette_use) {
            pal = vdp.pal_def;
        }
        var rgba = pal.rgba;
        if (use_grayscale ^ use_grayscale_tmp) {
            rgba = pal.gray; 
        }
        const pg_count = vdp.canvas_max_page;
        const sz = vdp.width / 2 * VDP.scan_line_count;
        let buf = vdp.imgData.data;
        let d = vdp.vram;
        let odx = 0, idx, px, c;
        let pg, i;

        for (pg = 0; pg < pg_count; ++pg) {
            idx = vdp.base.patnam
                    + vdp.mode_info.namsiz * pg;
            for (i = 0; i < sz; ++i) {
                px = d[idx];
                c = rgba[px >> 4];
                buf[ odx + 0 ] = c[0];
                buf[ odx + 1 ] = c[1];
                buf[ odx + 2 ] = c[2];
                buf[ odx + 3 ] = c[3];
                c = rgba[px & 15];
                buf[ odx + 4 ] = c[0];
                buf[ odx + 5 ] = c[1];
                buf[ odx + 6 ] = c[2];
                buf[ odx + 7 ] = c[3];
                odx += 8;
                idx += 1;
            }
        }
    }
    // ========================================================
    // 2ビットカラービットマップ プレーン処理
    // ========================================================
    update_bitmap4() {
    	const vdp = this;
        if (!vdp.imgData) {
            console.log('update_bitmap16 - this.imgData is null.');
            return;
        }
        let pal = vdp.palette;
        if (!palette_use) {
            pal = vdp.pal_def;
        }
        var rgba = pal.rgba;
        if (use_grayscale ^ use_grayscale_tmp) {
            rgba = pal.gray; 
        }
        const pg_count = vdp.canvas_max_page;
        const sz = vdp.width / 4 * VDP.scan_line_count;
        let buf = vdp.imgData.data;
        let d = vdp.vram;
        let odx = 0, idx, px, c;
        let pg, i, ix;
        const c_shift = [6,4,2,0];

        for (pg = 0; pg < pg_count; ++pg) {
            idx = vdp.base.patnam
                    + vdp.mode_info.namsiz * pg;
            for (i = 0; i < sz; ++i) {
                px = d[idx];
                for (ix = 0; ix < 4; ++ix) {
                    c = rgba[(px >> c_shift[ix]) & 3];
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
    // ========================================================
    // 8ビットカラービットマップ プレーン処理
    // ========================================================
    update_bitmap256() {
    	const vdp = this;
        if (!vdp.imgData) {
            console.log('update_bitmap256 - this.imgData is null.');
            return;
        }
        var rgba = vdp.pal256.rgba;
        if (use_grayscale ^ use_grayscale_tmp) {
            rgba = vdp.pal256.gray; 
        }
        const pg_count = vdp.canvas_max_page;
        const sz = vdp.width * VDP.scan_line_count;
        let buf = vdp.imgData.data;
        let d = vdp.vram;
        let odx = 0, idx, px, c;
        let pg, i;

        for (pg = 0; pg < pg_count; ++pg) {
            idx = vdp.base.patnam
                    + vdp.mode_info.namsiz * pg;
            for (i = 0; i < sz; ++i) {
                px = d[idx];
                c = rgba[px];
                buf[ odx + 0 ] = c[0];
                buf[ odx + 1 ] = c[1];
                buf[ odx + 2 ] = c[2];
                buf[ odx + 3 ] = c[3];
                odx += 4;
                idx += 1;
            }
        }
    }
    // ========================================================
    // YJKカラービットマップ プレーン処理
    // ========================================================
    update_bitmap_yjk() {
    	const vdp = this;

        if (!vdp.imgData) {
            console.log('update_bitmap_yjk - this.imgData is null.');
            return;
        }
        let y = [0,0,0,0];  // 0 ~ 31
        let j = 0;  // -32 ~ +31
        let k = 0;  // -32 ~ +31

        const pg_count = vdp.canvas_max_page;
        const sz = vdp.width * VDP.scan_line_count;
        let buf = vdp.imgData.data;
        let d = vdp.vram;
        let odx = 0, idx;
        let pg, i, h;

        for (pg = 0; pg < pg_count; ++pg) {
            idx = vdp.base.patnam
                    + vdp.mode_info.namsiz * pg;
            for (i = 0; i < sz; i+=4) {
                y[0] = d[idx] >> 3; k = d[idx] & 7;        ++idx;
                y[1] = d[idx] >> 3; k += (d[idx] & 7) * 8; ++idx;
                y[2] = d[idx] >> 3; j = d[idx] & 7;        ++idx;
                y[3] = d[idx] >> 3; j += (d[idx] & 7) * 8; ++idx;
                if (k > 31) k -= 64;
                if (j > 31) j -= 64;
                for (h = 0; h < 4; ++h) {
                    buf[odx + 0] = Math.floor( clamp(y[h] + j, 0, 31) * 255 / 31 );
                    buf[odx + 1] = Math.floor( clamp(y[h] + k, 0, 31) * 255 / 31 );
                    buf[odx + 2] = Math.floor( clamp(y[h] * 5 / 4 - j / 2 - k / 4, 0, 31) * 255 / 31 );
                    buf[odx + 3] = 255;
                    if (use_grayscale ^ use_grayscale_tmp) {
                        buf[odx + 0] = 
                        buf[odx + 1] = 
                        buf[odx + 2] = rgb_to_brightness( buf[odx + 0], buf[odx + 1], buf[odx + 2] );
                    }
                    odx += 4;
                }
            }
        }
    }
    // ========================================================
    // YJK+4ビットカラービットマップ プレーン処理
    // ========================================================
    update_bitmap_yae() {
    	const vdp = this;

        if (!vdp.imgData) {
            console.log('update_bitmap_yae - this.imgData is null.');
            return;
        }
        let y = [0,0,0,0];  // 0 ~ 31 / bit0 == 1 -> index color
        let j = 0;  // -32 ~ +31
        let k = 0;  // -32 ~ +31

        let pal = vdp.palette;
        if (!palette_use) {
            pal = vdp.pal_def;
        }
        var rgba = pal.rgba;
        if (use_grayscale ^ use_grayscale_tmp) {
            rgba = pal.gray; 
        }
        const pg_count = vdp.canvas_max_page;
        const sz = vdp.width * VDP.scan_line_count;
        let buf = vdp.imgData.data;
        let d = vdp.vram;
        let odx = 0, idx, c;
        let pg, i, h;

        for (pg = 0; pg < pg_count; ++pg) {
            idx = vdp.base.patnam
                    + vdp.mode_info.namsiz * pg;
            for (i = 0; i < sz; i+=4) {
                y[0] = d[idx] >> 3; k = d[idx] & 7;        ++idx;
                y[1] = d[idx] >> 3; k += (d[idx] & 7) * 8; ++idx;
                y[2] = d[idx] >> 3; j = d[idx] & 7;        ++idx;
                y[3] = d[idx] >> 3; j += (d[idx] & 7) * 8; ++idx;
                if (k > 31) k -= 64;
                if (j > 31) j -= 64;
                for (h = 0; h < 4; ++h) {
                    if (y[h] & 1) {
                        c = rgba[ y[h] >> 1 ];
                        buf[odx + 0] = c[0];
                        buf[odx + 1] = c[1];
                        buf[odx + 2] = c[2];
                        buf[odx + 3] = c[3];
                    } else {
                        buf[odx + 0] = Math.floor( clamp(y[h] + j, 0, 31) * 255 / 31 );
                        buf[odx + 1] = Math.floor( clamp(y[h] + k, 0, 31) * 255 / 31 );
                        buf[odx + 2] =  Math.floor( clamp(y[h]*5/4 - j/2 - k/4, 0, 31) * 255 / 31 );
                        buf[odx + 3] = 255;
                        if (use_grayscale ^ use_grayscale_tmp) {
                            buf[odx + 0] = 
                            buf[odx + 1] = 
                            buf[odx + 2] = rgb_to_brightness( buf[odx + 0], buf[odx + 1], buf[odx + 2] );
                        }
                    }
                    odx += 4;
                }
            }
        }
    }

    // ========================================================
    // ========================================================
    // お遊び要素
    // ========================================================
    // ========================================================

    // ========================================================
    // 色設定
    // ========================================================
    setColor( color )
    {
        const vdp = this;
        if (color === undefined) {
            color = 15;
            if (vdp.screen_no == 8) color = 0xff;
            if (vdp.screen_no == 10) color = 0xf0;
            if (vdp.screen_no == 11) color = 0xf0;
            if (vdp.screen_no == 12) color = 0xf8;
        }
        vdp.util.color = color;
    }

    // ========================================================
    // 1文字出力
    // ========================================================
    putChar( c, x, y, color ) {
        const vdp = this;
        let d = vdp.vram;
        const m = vdp.mode_info;
        const base = vdp.base;

        if (color === undefined) {
            color = vdp.util.color;
        }

        let txw = m.txw;
        let txh = (vdp.height + 7) >> 3; // height / 8;
        if (vdp.screen_no == 3) {
            txw = 32;
        }

        if (x < 0) return [x, y];
        if (y < 0) return [x, y];
        if (txw <= x) return [x, y];
        if (txh <= y) return [x, y];

   
        switch (vdp.screen_no) {
        case 0:
        case 1:
            {
                let a = x + y * m.txw;
                d[ base.patnam + a] = c;
            }
            break;
        case 2:
        case 4:
            {
                let a = ((x + y * m.txw) * 8);
                for (let i=0; i<8; ++i) {
                    d[ base.patgen + a++] = fontdat[c * 8 + i];
                }
            }
            break;
        case 3:
            {
                for (let i = 0; i < 8; ++i) {
                    let t = fontdat[c * 8 + i];
                    for (let j = 0; j < 4; ++j) {
                        let col = 0;
                        if (t & 0x80) col |= (color & 15) << 4;
                        t <<= 1;
                        if (t & 0x80) col |= (color & 15);
                        t <<= 1;
                        let a = (x * 4 + j) * 8
                              + y * txw * 32 + i;
                        d[ base.patgen + a ] = col;
                    }
                }
            }
            break;
        case 5:
        case 7:
            {
                const ls = (m.width * m.bpp) >> 3;
                for (let i = 0; i < 8; ++i) {
                    let t = fontdat[c * 8 + i];
                    for (let j = 0; j < 4; ++j) {
                        let col = 0;
                        if (t & 0x80) col |= (color << 4) & 0xf0;
                        t <<= 1;
                        if (t & 0x80) col |= (color) & 0x0f;
                        t <<= 1;
                        let a = (x * 4 + j)
                                + (y * 8 + i) * ls;
                        d[ base.patnam + a ] = col;
                    }
                }
            }
            break;
        case 6:
        case 9:
            {
                const ls = (m.width * m.bpp) >> 3;
                for (let i = 0; i < 8; ++i) {
                    let t = fontdat[c * 8 + i];
                    for (let j = 0; j < 2; ++j) {
                        let col = 0;
                        for (let k=0; k<4; ++k) {
                            col <<= 2;
                            if (t & 0x80) col |= color & 3;
                            t <<= 1;
                        }
                        let a = (x * 2 + j)
                                + (y * 8 + i) * ls;
                        d[ base.patnam + a ] = col;
                    }
                }
            }
            break;
        case 8:
        case 10:
        case 11:
        case 12:
            {
                const ls = (m.width * m.bpp) >> 3;
                for (let i = 0; i < 8; ++i) {
                    let t = fontdat[c * 8 + i];
                    for (let j = 0; j < 8; ++j) {
                        let col = 0;
                        if (t & 0x80) col |= color;
                        t <<= 1;
                        let a = (x * 8 + j)
                                + (y * 8 + i) * ls;
                        d[ base.patnam + a ] = col;
                    }
                }
            }
            break;
        }
        ++x;
        if (txw <= x) {
            x = 0;
            ++y;
        }
        return [x, y];
    }
    //------------------------
    // 文字列出力
    //------------------------
    print( s, x, y, color )
    {
        const vdp = this;
        if (x === undefined) {
            x = vdp.util.x;
        }
        if (y === undefined) {
            y = vdp.util.y;
        }
        let sp = s.split('\n');
        for (let l = 0; l < sp.length; ++l) {
            let m = toMSX_ankChar(sp[l]);
            for (let i = 0; i < m.length; ++i) {
                let a = vdp.putChar( m[i], x, y, color );
                x = a[0];
                y = a[1];
            }
            x = 0;
            ++y;
        }
        vdp.util.x = x;
        vdp.util.y = y;
    }
    //------------------------
    // patgenとpatcol補正：明るい色を1、暗い色を0にする
    //------------------------
    modifyPatternByBrightnessOrder()
    {
        const vdp = this;

        let pg,pg_count = 1;
        switch (vdp.screen_no) {
        case 1:
            pg_count = 1;
            break;
        case 2:
        case 4:
            pg_count = 3;
            break;
        default:
            // 対象外
            return;
        }

        let g = vdp.base.patgen;
        let c = vdp.base.patcol;
        let d = vdp.vram;
        let pal = vdp.palette.color;
        let i, y;
        let pat, pcol, cb, cf, bb, bf;
        for (pg = 0; pg < pg_count; ++pg) {
            for (i = 0; i < 256; ++i) {
                for (y = 0; y < 8; ++y, ++g, ++c) {
                    pcol = d[c];
                    cb = pcol >> 4;
                    cf = pcol & 15;
                    bb = pal[cb].brightness;
                    bf = pal[cf].brightness;
                    if (bf == bb ) {
                        if ((d[g] == 0) || (d[g] == 255)) {
                            if (bf < 128) {
                                d[g] = 0;
                            } else {
                                d[g] = 255;
                            }
                        }
                    } else
                    if (bf > bb) {
                        // 0と1入れ替え
                        d[g] = 255 ^ d[g];
                        d[c] = (cf << 4) + cb;
                    }
                }
            }
        }
    }
};

let vdp = null;


// ========================================================
// MSX ANK 文字 -> Unicode/S-JIS系変換
// in:  d - Uint8Array
// ========================================================
const char_table = Array.from(
    '　月火水木金土日年円時分秒百千万'
    + 'π┴┬┤├┼│─┌┐└┘×大中小'
    + ' !"#$%&\'()*+,-./0123456789:;<=>?'
    + '@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_'
    + '`abcdefghijklmnopqrstuvwxyz{|}~ '
    + '♠❤♣♦〇●をぁぃぅぇぉゃゅょっ'
    + '　あいうえおかきくけこさしすせそ'
    /*
    + ' ｡｢｣､･ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿ'
    + 'ﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ'
    */
    ///*
    + '　。「」、・ヲァィゥェォャュョッ'
    + 'ーアイウエオカキクケコサシスセソ'
    + 'タチツテトナニヌネノハヒフヘホマ'
    + 'ミムメモヤユヨラリルレロワン゛゜'
    //*/
    + 'たちつてとなにぬねのはひふへほま'
    + 'みむめもやゆよらりるれろわん　■'
);
const dakuten_list = [
    'がぎぐげござじずぜぞだぢづでどばびぶべぼガギグゲゴザジズゼゾダヂヅデドバビブベボ',
    'かきくけこさしすせそたちつてとはひふへほカキクケコサシスセソタチツテトハヒフヘホ'
];
const handakuten_list = [
    'ぱぴぷぺぽパピプペポ',
    'はひふへほハヒフヘホ',
];
const c_dakuten = char_table.indexOf( '゛' );
const c_handaku = char_table.indexOf( '゜' );
function fromMSX_ankChar(d)
{
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
function toMSX_ankChar(s)
{

    let res = new Uint8Array(s.length * 2);
    let o = 0;
    for (i = 0; i < s.length; ++i) {
        let mj = s.charAt(i);
        let i_dakuten = dakuten_list[0].indexOf( mj );
        let i_handaku = handakuten_list[0].indexOf( mj );
        if (-1 < i_dakuten) {
            let c = char_table.indexOf( dakuten_list[1].charAt(i_dakuten) );
            if (c < 0) continue;
            res[o++] = c;
            res[o++] = c_dakuten;
        }else
        if (-1 < i_handaku) {
            let c = char_table.indexOf( handakuten_list[1].charAt(i_handaku) );
            if (c < 0) continue;
            res[o++] = c;
            res[o++] = c_handaku;
        }else
        {
            let c = char_table.indexOf( mj );
            if (c < 0) continue;
            res[o++] = c;
        }
    }
    return res.slice(0, o);
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
// 設定保存
// ========================================================
const config_name = 'gsrle_html_view_config';
function saveConfig()
{
    let config = 
    {
        name: config_name,
        vdp:
        {
            screen_no       : vdp.screen_no,
            txw             : vdp.mode_info.txw,
            interlace_mode  : vdp.interlace_mode,
            disp_page       : vdp.disp_page,
            sprite_disable  : vdp.sprite_disable,
            aspect_ratio    : vdp.aspect_ratio,
            force_height    : vdp.force_height,

            sprite16x16     : vdp.sprite16x16,
            sprite_double   : vdp.sprite_double,

            base:
            {
                patnam      : vdp.base.patnam,
                patgen      : vdp.base.patgen,
                patcol      : vdp.base.patcol,

                spratr      : vdp.base.spratr,
                sprpat      : vdp.base.sprpat,
            },
         },
        
        save_cg4000         : save_cg4000,
        quick_save_mode     : quick_save_mode,
        palette_use         : palette_use,
        pal_not_use_vram    : pal_not_use_vram,
        pal_use_tms9918     : pal_use_tms9918,
        use_grayscale       : use_grayscale,
        sprite_limit_mode   : sprite_limit_mode,
        sprgen_bg_type      : sprgen_bg_type,
        vram_interleave     : vram_interleave,
    };

    let filename = config.name + '.json';

    let json_data = JSON.stringify( config, null, '    ' );
    //console.log(json_data);

    const blob = new Blob( [json_data], { "type" : "text/plain" });
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
// 設定読み込み
// ========================================================
function getParam( obj, name, def ) {
    return (name in obj) ? obj[name] : def;
}
function loadConfig( d, file_text )
{
    let c = null;
    try {
        c = JSON.parse( d );
    } catch( err ) {
        add_log( '"' + file_text + '": 読み込みエラー\n' + err );
        return false;
    }
    if (!('name' in c)) {
        return false;
    }
    if (c.name != config_name) {
        console.log('設定名が違います');
        return false;
    }
    if ('vdp' in c) {
        let cv = c.vdp;
        vdp.sprite_disable = getParam(cv, 'sprite_disable', vdp.sprite_disable);
        vdp.aspect_ratio = getParam(cv, 'aspect_ratio', vdp.aspect_ratio);
        setCheckedRadioSwitch( 'stretch_screen', vdp.aspect_ratio );
        vdp.force_height = getParam(cv, 'force_height', vdp.force_height);
        setCheckedRadioSwitch( 'height_mode', vdp.force_height );

        if (('screen_no' in cv) ||
            ('txw' in cv) ||
            ('interlace_mode' in cv) ||
            ('force_height' in cv)
        ) {
            let disp_height = vdp.force_height ? vdp.force_height : vdp.auto_height;

            vdp.changeScreen(
                getParam( cv, 'screen_no', vdp.screen_no),
                getParam( cv, 'txw', vdp.txw),
                getParam( cv, 'interlace_mode', vdp.interlace_mode),
                disp_height
            );
        }

        if ('disp_page' in cv) {
            vdp.setPage( cv.disp_page );
        }

        vdp.sprite16x16 = getParam(cv, 'sprite16x16', vdp.sprite16x16);
        vdp.sprite_double = getParam(cv, 'sprite_double', vdp.sprite_double);

        if ('base' in cv) {
            let cvb = cv.base;
            if ('patnam' in cvb) {
                vdp.setPatternNameTable( cvb.patnam );
            }
            if ('patgen' in cvb) {
                vdp.setPatternGeneratorTable( cvb.patgen );
            }
            if ('patcol' in cvb) {
                vdp.setPatternColorTable( cvb.patcol );
            }

            if ('spratr' in cvb) {
                vdp.setSpriteAttributeTable( cvb.spratr );
            }
            if ('sprpat' in cvb) {
                vdp.setSpritePatternTable( cvb.sprpat );
            }
        }
    }

    save_cg4000_chk.checked = 
    save_cg4000 = getParam( c, 'save_cg4000', save_cg4000);

    quick_save_mode = getParam( c, 'quick_save_mode', quick_save_mode);
    setCheckedRadioSwitch( 'qick_save', quick_save_mode );

    sprite_limit_mode = getParam( c, 'sprite_limit_mode', sprite_limit_mode);
    setCheckedRadioSwitch( 'sprite_limit_mode', sprite_limit_mode );

    pal_not_use_vram_chk.checked = 
    pal_not_use_vram = getParam( c, 'pal_not_use_vram', pal_not_use_vram);
    pal_use_tms9918_chk.checked = 
    pal_use_tms9918 = getParam( c, 'pal_use_tms9918', pal_use_tms9918);

    pal_grayscale_chk.checked = 
    use_grayscale = getParam( c, 'use_grayscale', use_grayscale);

    sprgen_bg_type = getParam( c, 'sprgen_bg_type', sprgen_bg_type);
    transparent_bg_chk.checked = (0 < sprgen_bg_type);
    setTransparentBg(canvas_sprgen, sprgen_bg_type);

    palette_use_chk2.checked = 
    palette_use_chk.checked = 
    palette_use = getParam( c, 'palette_use', palette_use);

    vram_interleave_chk.checked = getParam( c, 'vram_interleave', vram_interleave);

    vdp.updateDefaultColorPalette();
    vdp.update();
    vdp.draw();
    return true;
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
    if (bmp_file.size) {
        f = bmp_file;
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
        if (page < 0) {
            size = f.size;
            page = 0;
            if (vdp.mode_info.bpp < 1) {
                // SCREEN 0～4
                // SCREEN4以下の場合は表示ページを対象とする
                page = vdp.disp_page;
                if (save_cg4000) {
                    // VRAM 0x0000～0x3FFFまるごとセーブ
                    size = Math.max(size, vdp.mode_info.block_size);
                }
            }
        } else {
            if (vdp.mode_info.bpp < 1) {
                // SCREEN 0～4
                if (save_cg4000) {
                    // VRAM 0x0000～0x3FFFまるごとセーブ
                    size = vdp.mode_info.block_size;
                } else {
                    // BinHeaderの範囲だけセーブ
                    start = f.header.start;
                    size = f.header.end - f.header.start + 1;
                    // SCREEN4以下の場合は表示ページを対象とする
                    page += vdp.disp_page;
                }
            } else
            if (vdp.mode_info.bpp) {
                size = vdp.height * vdp.mode_info.bpp * vdp.width / 8;
            }
            let end = start + size - 1;
            if (with_pal) {
                let withpal_end = vdp.mode_info.palend + 1;
                if (end < withpal_end) {
                    end = withpal_end;
                    size = withpa_end - start + 1;
                }
                if (withpal_end <= end) {
                    vdp.vram.set( vdp.getPalTbl(), vdp.mode_info.paltbl );
                }
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
            force_height = VDP.scan_line_count;
        } else
        if (mode_info.palend < end) {
            // リニア形式はパレットテーブルを越えているかで判断
            force_height = VDP.scan_line_count;
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
//      ext_info - file info
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
    vdp.auto_height = detectImageHeight( mode_info, header, dat.length );
    let disp_height = vdp.force_height ? vdp.force_height : vdp.auto_height;

    if ((ext_info.page < 0) && (ext_info.interlace < 0)) {
    } else
    if ((ext_info.page != 0) &&
         (ext_info.interlace != 0) &&
         (info.screen_no == vdp.screen_no) &&
         (info.interlace == vdp.interlace_mode) &&
         (disp_height == vdp.height)
       ) {
    } else {
        vdp.changeScreen( info.screen_no, info.txw, info.interlace );
        vdp.cls( info.screen_no != vdp.screen_no );
    }
    if (!ext_info || !ext_info.page) {
        vdp.cls();
    }

    vdp.loadBinary(dat, 
        header.start + info.page * vdp.mode_info.page_size);

    // VRAMパレットテーブル読み込み
    //if (4 <= vdp.screen_no) { // スクリーン4以上の場合のみ
        if (header.isBinary && !header.isCompress) {
            if (!ext_info.page && (header.end >= vdp.mode_info.palend)) {
                if (!pal_not_use_vram) {
                    vdp.restorePalette(); 
                }
            }
        }
    //}
    vdp.update();
    vdp.draw();

    return header;
}

// ========================================================
// COPY文で保存された画像読み込み

// in:  buf - Uint8Array
//      ext_info - file info
//      file_text - filename
// ========================================================
function loadCpy(buf, ext_info, file_text)
{
    let width = get_u16(buf, 0);
    let height = get_u16(buf, 2);
    let d = buf.subarray( 4 );

    vdp.auto_height = 212 < height ? 256 : 212;
    let screen_no = ext_info.screen_no < 0 ? vdp.screen_no : ext_info.screen_no;

    if (screen_no < 5) {
        add_log( '"' + file_text + '": COPY画像はSCREEN4以下では読み込めません。' );
        return 0;
    }

    vdp.changeScreen( screen_no );
    vdp.cls();

    let x,y,xi,mi;
    let vram = vdp.vram;
    let screen_width  = vdp.mode_info.width;
    let screen_height = vdp.mode_info.height;
    let line_size = vdp.mode_info.bpp * screen_width / 8;

    let n = 0;
    let i = 0;
    if (vdp.mode_info.bpp == 4) {
        const mask = [0xf0, 0x0f];
        for (y = 0; y < height; ++y) {
            if (y < screen_height) {
                xi = n;
                for (x = 0; x < width; ++x) {
                    if (x < screen_width) {
                        mi = x & 1;
                        if (i < d.length) {
                            vram[xi] = (vram[xi] & mask[1-mi]) | (d[i] & mask[mi]);
                        }
                    }
                    xi += mi;
                    i += mi;
                }
            }
            i += width & 1;
            n += line_size;
        }
    } else {
        const mask = [0xf0, 0x0f];
        for (y = 0; y < height; ++y) {
            if (y < screen_height) {
                xi = n;
                for (x = 0; x < width; ++x) {
                    if (x < screen_width) {
                        if (i < d.length) {
                            vram[xi] = d[i];
                        }
                    }
                    ++xi;
                    ++i;
                }
            }
            n += line_size;
        }
    }
    vdp.update();
    vdp.draw();

    return n;
}

// ========================================================
// BMP読み込み (OpenMSXのvram2bmpで出力した物)
//  
//  openMSXでF10→コンソール
//      vram2bmp vram.bmp 0 256 2024
//      とするとVRAM全域セーブになる。
//      16bitビットマップモードではパレットも保存される。
//
// in:  d - Uint8Array
//      ext_info - file info
//      file_text - filename
// ========================================================
function loadBmp(d, ext_info, file_text)
{
    // ========================================================
    // バイナリ解析開始
    // ========================================================
    class BITMAPFILEHEADER  {
        [Symbol.toStringTag] = 'BITMAPFILEHEADER';
        constructor( d ) {
            this.length = 14;
            this.bfType = 'BM';     // +0 : 2 bytes
            this.bfSize = 0;        // +2 : 4 bytes
            this.bfReserved1 = 0;   // +6 : 2 bytes
            this.bfReserved1 = 0;   // +8 : 2 bytes
            this.bfOffBits = 0;     // +10: 4 bytes
            this.error = false;
            this.setd( d );
        }
        setd( d )
        {
            if (d === undefined) return true;
            if (d.constructor !== Uint8Array) {
                add_log( '"' + file_text + '": Uint8Arrayではありません。' );
                this.error = true;
                return false;
            }

            if ((d[0] != this.bfType.charCodeAt(0)) ||
                (d[1] != this.bfType.charCodeAt(1))) 
            {
                add_log( '"' + file_text + '": BMPファイルではありません。' );
                this.error = true;
                return false;
            }
            this.bfSize = get_u32(d, 2);
            this.bfOffBits = get_u32(d, 10);
            return true;
        }
    }
    class BITMAPINFOHEADER {
        [Symbol.toStringTag] = 'BITMAPINFOHEADER';
        constructor( d ) {
            this.length = 40;
            this.bcSize = 0;        // +0 : 4 bytes
            this.bcWidth = 0;       // +4 : 4 bytes
            this.bcHeight = 0;      // +8 : 4 bytes
            this.bcPlanes = 0;      // +12: 2 bytes
            this.bcBitCount = 0;    // +14: 2 bytes
            this.biCompression = 0; // +16: 4 bytes
            this.biSizeImage = 0;   // +20: 4 bytes
            this.biXPixPerMeter = 0;// +24: 4 bytes
            this.biYPixPerMeter = 0;// +28: 4 bytes
            this.biClrUsed = 0;     // +32: 4 bytes
            this.biCirImportant = 0;// +36: 4 bytes
            this.error = false;
            this.setd( d );
        }
        setd( d ) {
            if (d === undefined) return true;
            if (d.constructor !== Uint8Array) {
                add_log( '"' + file_text + '": Uint8Arrayではありません。' );
                this.error = true;
                return false;
            }
            this.bcSize = get_u32(d, 0);        // +0 : 4 bytes
            if (this.bcSize != this.length) {
                add_log( '"' + file_text + '": BITMAPINFOHEADERではありません。' );
                this.error = true;
                return false;
            }
            this.bcWidth = get_u32(d, 4);       // +4 : 4 bytes
            this.bcHeight = get_u32(d, 8);      // +8 : 4 bytes
            this.bcPlanes = get_u16(d,12);      // +12: 2 bytes
            this.bcBitCount = get_u16(d,14);    // +14: 2 bytes
            this.biCompression = get_u32(d,16); // +16: 4 bytes
            if (this.biCompression) {
                add_log( '"' + file_text + '": 非対応の圧縮形式です。' );
                this.error = true;
                return false;
            }
            this.biSizeImage = get_u32(d,20);   // +20: 4 bytes
            this.biXPixPerMeter = get_u32(d,24);// +24: 4 bytes
            this.biYPixPerMeter = get_u32(d,28);// +28: 4 bytes
            this.biClrUsed = get_u32(d,32);     // +32: 4 bytes
            this.biCirImportant = get_u32(d,36);// +36: 4 bytes
            return true;
        }
    }

    //=================================
    let file_header = new BITMAPFILEHEADER( d );
    let info_header = new BITMAPINFOHEADER( d.subarray( file_header.length ) );
    if (file_header.error || info_header.error) {
        return 0;
    }

    // 高さ指定
    vdp.auto_height = 256;
    vdp.changeScreen( vdp.screen_no, vdp.mode_info.txw, vdp.interlace_mode );

    // パレット RGBQUAD BGR0_8888
    let pal_s = file_header.length + info_header.length;
    let pal_size = file_header.bfOffBits - pal_s;
    if (pal_size >= 16 * 4) {
        let pal = d.subarray( pal_s, file_header.bfOffBits );
        let i = 0;
        for (let ci = 0; ci < 16; ++ci, i+=4) {
            vdp.palette.color[ci].setRgb888( pal[i + 2], pal[i + 1], pal[i + 0] );
        }
        vdp.palette.makeRgba();
    }

    // ピクセルデータ
    let dat = d.subarray( file_header.bfOffBits );

    //if ((info_header.biCompression == 2) || // BI_RLE8
    //    (info_header.biCompression == 3))   // BI_RLE4
    //{
    //    // 圧縮の場合 end = 展開後のピクセルサイズ
    //    // dat = gs_rle_decode( dat, header.end );
    //    // 例外もありうるので一旦無視して上限をVRAMサイズ
    //    // 実際に展開したサイズまでのデータを返す
    //    dat = gs_rle_decode( dat );
    //}

    let trans_size = Math.min( dat.length , vdp.vram.length );
    vdp.vram.set( dat.subarray( 0, trans_size ) );

    vdp.update();
    vdp.draw();

    return trans_size;
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
    let is_config = (file_ext == 'JSON');
    let is_pal = isPaletteFile(file_ext);
    let ext_info = getExtInfo(file_ext);
    if (!ext_info && !is_pal && !is_config)
    {
        // 画像ファイルでなければ無視
        add_log( '"' + file_text + '": 画像ファイルではありません。' );
        return false;
    }

    // カレントファイル表示処理
    if (is_config) {

    } else
    if (is_pal) {
        // パレット
        pal_file = LogFile( target_file );
    } else
    if (ext_info.type == 3) { // .CPY
        // COPY 画像
        pal_file = empty_file;
        sub_file = empty_file;
        main_file = empty_file;
        bmp_file = LogFile( target_file );
        vdp.cls();
    } else 
    if (ext_info.type == 2) { // .BMP
        // BMP / RAW 画像
        pal_file = empty_file;
        sub_file = empty_file;
        main_file = empty_file;
        bmp_file = LogFile( target_file );
        vdp.cls();
    } else 
    if ((ext_info.interlace < 0) || (ext_info.interlace < 0)) {
        // 現在とフォーマットが違う場合はクリア
        if (((ext_info.screen_no >= 0) && (vdp.screen_no != ext_info.screen_no)) ||
            ((ext_info.interlace >= 0) && (vdp.interlace_mode != ext_info.interlace)))
        {
            pal_file = empty_file;
            sub_file = empty_file;
            main_file = empty_file;
            bmp_file = empty_file;
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
            bmp_file = empty_file;
            vdp.cls();
        }
        // 追加画像
        sub_file = LogFile( target_file );
    } else 
    {
        // メイン画像
        pal_file = empty_file;
        sub_file = empty_file;
        bmp_file = empty_file;
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
        if (is_config) {
            if (loadConfig( f.target.result, file_text ))
            {
                add_log( '"' + file_text + '": 読み込み完了' );
            }
        } else {
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
                } else
                if (ext_info.type == 3) { // .CPY
                    let ts = loadCpy(u8array, ext_info, file_text);
                    if (ts <= 0) {
                        // エラー
                        bmp_file = empty_file;
                        file_load_que.length = 0;    //残りをすべて破棄
                        drop_avilable = true;
                        displayCurrentFilename();
                        return;
                    }
                    let h = new BinHeader();
                    h.id    = BinHeader.HEAD_ID_LINEAR;
                    h.start = 0;
                    h.end   = ts - 1;
                    h.run   = 0;
                    bmp_file.header = h;
                    bmp_file.size = ts - 1;
                } else
                if (ext_info.type == 2) { // .BMP
                    let ts = loadBmp(u8array, ext_info, file_text);
                    if (ts <= 0) {
                        // エラー
                        bmp_file = empty_file;
                        file_load_que.length = 0;    //残りをすべて破棄
                        drop_avilable = true;
                        displayCurrentFilename();
                        return;
                    }
                    let h = new BinHeader();
                    h.id    = BinHeader.HEAD_ID_LINEAR;
                    h.start = 0;
                    h.end   = ts - 1;
                    h.run   = 0;
                    bmp_file.header = h;
                    bmp_file.size = ts - 1;
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
            if (need_save_all)
            {
                // 全て完了した後
                // 自動保存があれば実行
                saveAll();
            }
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
        need_save_all = false;
    };

    drop_avilable = false;
    if (is_config) {
        reader.readAsText(target_file, 'UTF-8');
    } else {
        reader.readAsArrayBuffer(target_file);
    }

    return true;
}


// ========================================================
//  複数ファイル読み込み
// ========================================================
function openFiles( files )
{
    let config = [];
    let main = [];
    let sub = [];
    let pal = [];

    for (var i = 0; i < files.length; ++i) {

        let file_ext = getExt(files[i].name);
        let is_config = (file_ext == 'JSON');
        let is_pal = isPaletteFile(file_ext);
        let ext_info = getExtInfo(file_ext);

        if (is_config) {
            config.push( files[i] );
        } else
        if (is_pal) {
            pal.push( files[i] );
            need_save_all = true;
        } else
        if (ext_info) {
            if (ext_info.interlace && ext_info.page) {
                sub.push( files[i] );
                need_save_all = true;
            } else {
                main.push( files[i] );
                need_save_all = true;
            }
        } else {
            add_log( '"' + files[i].name + '": 読み込み対象ファイルではありません' );
        }

    }

    // 手抜き：
    // 待機チェーンで連続ロードする
    let result = true;
    file_load_que = config.concat( main, sub, pal );

    if (file_load_que.length) {
        openGsFile( file_load_que.shift() );
    }
    return true;
}

// ========================================================
// 全て保存
// ========================================================
function saveAll( commpress, with_pal )
{
    need_save_all = false;
    if (commpress === undefined)
    {
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
    }

    let f = null;
    if (bmp_file.size && bmp_file.name.length) {
        saveImage( bmp_file, -1, commpress, with_pal );
    } else {
        if (main_file.size && main_file.name.length) {
            saveImage( main_file, 0, commpress, with_pal );
        }
        if (sub_file.size && sub_file.name.length) {
            saveImage( sub_file, 1, commpress, with_pal );
        }
    }
    if (!with_pal) {
        savePalette();
    }
}

// ========================================================
//  透明背景の設定
//  e: element
//  t: タイプ 0 か 1
// ========================================================
function setTransparentBg(e, t)
{
    switch (t) {
    case 0: // 明るめのクロスハッチ
        e.style['background-image'] = 
        'linear-gradient(45deg, #aaa 25%, transparent 25%, transparent 75%, #aaa 75%),' + 
        'linear-gradient(45deg, #aaa 25%, transparent 25%, transparent 75%, #aaa 75%)';
        e.style['background-position'] = '0 0, 16px 16px';
        e.style['background-size'] = '32px 32px';
        e.style['background-color'] = 'gray';
        break;
    case 1: // 暗めのクロスハッチ
        e.style['background-image'] = 
        'linear-gradient(45deg, #444 25%, transparent 25%, transparent 75%, #444 75%),' + 
        'linear-gradient(45deg, #444 25%, transparent 25%, transparent 75%, #444 75%)';
        e.style['background-position'] = '0 0, 16px 16px';
        e.style['background-size'] = '32px 32px';
        e.style['background-color'] = '#333';
        break;
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

    // ========================================================
    //  HTMLパーツ
    // ========================================================
    // --------------------------------------------------------
    // 描画エリア
    // --------------------------------------------------------
    const canvas_area  = document.getElementById('canvas_area');
    const canvas_page0 = document.getElementById('canvas_page0');
    const canvas_page1 = document.getElementById('canvas_page1');
    const canvas_page2 = document.getElementById('canvas_page2');
    const canvas_page3 = document.getElementById('canvas_page3');

    const palette_area = document.getElementById('palette_area');

    const canvas_patgen = document.getElementById('canvas_patgen');
    const canvas_sprgen = document.getElementById('canvas_sprgen');

    //const drop_area    = document.getElementById('drop_area');
    //const drop_area    = canvas_area;
    const drop_area    = document.body;

    // --------------------------------------------------------
    // 読み込みファイル一覧
    // --------------------------------------------------------
    const filename_area = document.getElementById('filename_area');
    const filename_area2 = document.getElementById('filename_area2');
    const filename_area3 = document.getElementById('filename_area3');

    // --------------------------------------------------------
    // ログメッセージ
    // --------------------------------------------------------
    const log_text = this.document.getElementById('log_text');

    // --------------------------------------------------------
    // 画面SPEC
    // --------------------------------------------------------
    //const spec_details             = document.getElementById('spec_details'); // div
    const sel_screen_no             = document.getElementById('sel_screen_no');  // select
    const screen_interlace_chk      = document.getElementById('screen_interlace_chk'); // check
    const sel_disp_page             = document.getElementById('sel_disp_page');  // select
    const sprite_use_chk            = document.getElementById('sprite_use_chk'); // check
    const label_sprite_use          = document.getElementById('label_sprite_use');

    const detail_screen_mode_name   = document.getElementById('detail_screen_mode_name');  // span
    const detail_screen_width       = document.getElementById('detail_screen_width');  // span
    const detail_screen_height      = document.getElementById('detail_screen_height');  // span
    const detail_interlace          = document.getElementById('detail_interlace');  // span
    const detail_sprite_on          = document.getElementById('detail_sprite_on');  // span

    // --------------------------------------------------------
    // スクロール
    // --------------------------------------------------------
    const detail_vscroll            = document.getElementById('detail_vscroll');  // button
    const detail_hscroll            = document.getElementById('detail_hscroll');  // button
    const hscroll_mask_chk          = document.getElementById('hscroll_mask_chk');  // checkbox
    const hscroll_2page_chk         = document.getElementById('hscroll_2page_chk');  // checkbox
    detail_vscroll.style.width = `${detail_vscroll.clientWidth + 4}px`;
    detail_hscroll.style.width = `${detail_hscroll.clientWidth + 4}px`;
    
    // --------------------------------------------------------
    // ファイル情報詳細
    // --------------------------------------------------------
    const label_pal_file    = document.getElementById('label_pal_file');
    const detail_pal_file   = document.getElementById('detail_pal_file');
    const detail_page0_file = document.getElementById('detail_page0_file');
    const detail_page1_file = document.getElementById('detail_page1_file');
    const detail_page0_spec = document.getElementById('detail_page0_spec');
    const detail_page1_spec = document.getElementById('detail_page1_spec');

    // --------------------------------------------------------
    // 詳細情報ブロック
    // --------------------------------------------------------
    const detail_page0     = document.getElementById('detail_page0' );
    const detail_page1     = document.getElementById('detail_page1' );
    const detail_page2     = document.getElementById('detail_page2' );
    const detail_page3     = document.getElementById('detail_page3' );
    const detail_chrgen    = document.getElementById('detail_chrgen');
    const detail_sprgen    = document.getElementById('detail_sprgen');

    const tab_detail_chrgen = document.getElementById('tab_detail_chrgen');
    const tab_detail_sprgen = document.getElementById('tab_detail_sprgen');

    const detail_chrgen_spec = document.getElementById('detail_chrgen_spec');
    const detail_sprgen_spec = document.getElementById('detail_sprgen_spec');

    // --------------------------------------------------------
    // 保存ボタン
    // --------------------------------------------------------
    const pal_save            = document.getElementById('pal_save');
    const tab_save_all        = document.getElementById('tab_save_all');
    const all_save_bsave      = document.getElementById('all_save_bsave');
    const all_save_bsave_np   = document.getElementById('all_save_bsave_np');
    const all_save_gsrle      = document.getElementById('all_save_gsrle');
    const page0_save_group    = document.getElementById('page0_save_group');
    const page1_save_group    = document.getElementById('page1_save_group');
    const page2_save_group    = document.getElementById('page2_save_group');
    const page3_save_group    = document.getElementById('page3_save_group');
    const page0_save_bsave    = document.getElementById('page0_save_bsave');
    const page0_save_bsave_np = document.getElementById('page0_save_bsave_np');
    const page0_save_gsrle    = document.getElementById('page0_save_gsrle');
    const page1_save_bsave    = document.getElementById('page1_save_bsave');
    const page1_save_bsave_np = document.getElementById('page1_save_bsave_np');
    const page1_save_gsrle    = document.getElementById('page1_save_gsrle');
    const page2_save_bsave    = document.getElementById('page2_save_bsave');
    const page2_save_bsave_np = document.getElementById('page2_save_bsave_np');
    const page2_save_gsrle    = document.getElementById('page2_save_gsrle');
    const page3_save_bsave    = document.getElementById('page3_save_bsave');
    const page3_save_bsave_np = document.getElementById('page3_save_bsave_np');
    const page3_save_gsrle    = document.getElementById('page3_save_gsrle');

    // 設定保存ボタン
    const config_save         = document.getElementById('config_save');

    // --------------------------------------------------------
    // ファイルを開くボタン
    // --------------------------------------------------------
    const file_open_button = document.getElementById("file_open");
    const file_open_label = this.document.getElementById("file_open_label");


    // --------------------------------------------------------
    // SCREEN 4以下で0x0000～0x3FFF全体保存
    // --------------------------------------------------------
    const save_cg4000_chk = document.getElementById('save_cg4000_chk');

    // --------------------------------------------------------
    // 自動保存
    // --------------------------------------------------------
    const quick_save = document.getElementsByName('qick_save');

    // --------------------------------------------------------
    // 情報表示
    // --------------------------------------------------------
    const help_guide = document.getElementById('help_guide');

    // --------------------------------------------------------
    // アコーディオンタブ
    // --------------------------------------------------------
    const tab_title = document.getElementById('tab_title'); // help detail tag
    const tab_helps = document.getElementById('tab_helps'); // help detail tag
    const tab_settings = document.getElementById('tab_settings'); // settings detail tag

    // --------------------------------------------------------
    // スプライトの横並び制限解除
    // --------------------------------------------------------
    const sprite_limit_mode_radio = document.getElementsByName('sprite_limit_mode');
    
    // --------------------------------------------------------
    // カラーパレット
    // --------------------------------------------------------
    // カラーパレットをVRAMから読み込まない
    const pal_not_use_vram_chk = document.getElementById('pal_not_use_vram_chk');

    // カラーパレット未使用時にTMS9918Aの色にする
    const pal_use_tms9918_chk = document.getElementById('pal_use_tms9918_chk');

    // グレースケールで表示する
    const pal_grayscale_chk = document.getElementById('pal_grayscale_chk');

    // カラーパレット有効/無効
    const palette_use_chk = document.getElementById('palette_use_chk');
    const palette_use_chk2 = document.getElementById('palette_use_chk2');

    // --------------------------------------------------------
    // VRAM接続
    // --------------------------------------------------------
    const vram_interleave_chk = document.getElementById('vram_interleave_chk');
    
    // --------------------------------------------------------
    // 画面表示設定
    // --------------------------------------------------------
    // ドットアスペクト比
    const stretch_screen_radio = document.getElementsByName('stretch_screen');

    // 画面縦サイズモード
    const height_mode_radio = document.getElementsByName('height_mode');

    // --------------------------------------------------------
    // キャラクタジェネレータ設定
    // --------------------------------------------------------
    const sel_patnam_page = document.getElementById('sel_patnam_page');
    const sel_patnam_ofs  = document.getElementById('sel_patnam_ofs');
    const sel_patgen_page = document.getElementById('sel_patgen_page');
    const sel_patgen_ofs  = document.getElementById('sel_patgen_ofs');
    const sel_patcol_page = document.getElementById('sel_patcol_page');
    const sel_patcol_ofs  = document.getElementById('sel_patcol_ofs');
    const sel_patcol_group = document.getElementById('sel_patcol_group');

    const patgen_chk = document.getElementById('patgen_chk');
    const patcol_chk = document.getElementById('patcol_chk');

    // --------------------------------------------------------
    // スプライト設定
    // --------------------------------------------------------
    const sel_sprite_mode = document.getElementById('sel_sprite_mode');
    const sel_spratr_page = document.getElementById('sel_spratr_page');
    const sel_spratr_ofs  = document.getElementById('sel_spratr_ofs');
    const sel_sprpat_page = document.getElementById('sel_sprpat_page');
    const sel_sprpat_ofs  = document.getElementById('sel_sprpat_ofs');

    const transparent_bg_chk = document.getElementById('transparent_bg_chk');

    // --------------------------------------------------------
    // キャンバススムージング
    // --------------------------------------------------------
    //const canvas_smoothing = document.getElementById('canvas_smoothing');

    // ========================================================
    // UIイベント処理
    //  リロード時に初期状態が変わるブラウザがあるので
    //  現時点でのINPUTコントロールの状態を見て反映する事
    // ========================================================
    // --------------------------------
    // 画面モード
    // --------------------------------
    removeAllSelectOption( sel_screen_no );
    for (let i = 0; ; ++i) {
        let m = VDP.getScreenModeSettingByIdx(i);
        if (!m) break;
        let o = addSelectOption(sel_screen_no, 
            `SCREEN ${m.no}${(m.no==0) && (m.txw==80) ? '-2' : ''}`,  i);
        // BASICでは区別されるがVDP上では同じモードを非表示
        if ((m.no==9) || (m.no==11)) {
            o.style.display = 'none'; // 表示は'block'
        }
    }
    sel_screen_no.addEventListener('change',
    function(ev) {
        let e = ev.target;
        let i = parseInt(e.options[e.selectedIndex].value);
        if (0 <= i) {
            let m = VDP.getScreenModeSettingByIdx(i);
            vdp.changeScreen(m.no, m.txw, vdp.interlace_mode );
            //vdp.cls();
            vdp.update();
            vdp.draw();
            displayCurrentFilename();
        }
    });
    // --------------------------------
    // インターレースモード
    // --------------------------------
    screen_interlace_chk.addEventListener('change',
    function(ev) {
        let e = ev.target;
        let i = e.checked ? 1 : 0;
        vdp.setInterlaceMode( i );
        //vdp.cls();
        vdp.update();
        vdp.draw();
        displayCurrentFilename();
    });
    // --------------------------------
    // 表示ページ
    // --------------------------------
    sel_disp_page.addEventListener('change',
    function(ev) {
        let e = ev.target;
        let i = parseInt(e.options[e.selectedIndex].value);
        if (0 <= i) {
            vdp.setPage(i);
            vdp.update();
            vdp.draw();
            displayCurrentFilename();
        }
    });

    // ========================================================
    // vdpにキャンバスを指定
    // ========================================================
    vdp = new VDP({
        canvas:         canvas_area,
        pal_canvas:     palette_area,
        page_canvas:    [canvas_page0, canvas_page1, canvas_page2, canvas_page3],
        patgen_canvas:  canvas_patgen,
        sprgen_canvas:  canvas_sprgen
    });

    //log_text.innerText = '';
    default_log_html = help_guide.innerHTML;
    
    // --------------------------------
    // イベント：スプライト非表示
    // --------------------------------
    if (sprite_use_chk) {
        sprite_use_chk.addEventListener('change',
        function(ev) {
            let e = ev.target;
            vdp.sprite_disable = e.checked ? 0 : 1;
            vdp.update();
            vdp.draw();
            displaySpriteInfo();
        });
        vdp.sprite_disable = sprite_use_chk.checked ? 0 : 1;
    }

    // ========================================================
    // イベント：画面縦横比(DotAspect比)変更
    // ========================================================
    canvas_area.height = VDP.screen_height;
    function changeStrechMode(e) { 
        if (e.checked) {
            vdp.aspect_ratio = Number.parseFloat(e.value);
            vdp.draw();
        }
    }
    stretch_screen_radio.forEach(e => { changeStrechMode(e); });
    let onChangeStrechMode = function(event) {
        changeStrechMode( event.target );
    }
    stretch_screen_radio.forEach(e => {
        e.addEventListener("change", onChangeStrechMode );
    });

    // ========================================================
    // イベント：画面縦サイズモード変更
    // ========================================================
    function changeHeightMode(e) {
        if (e.checked) {
            vdp.force_height = Number.parseInt(e.value);
            vdp.changeScreen( vdp.screen_no, vdp.mode_info.txw, vdp.interlace_mode );
            vdp.update();
            vdp.draw();
        }
    }
    height_mode_radio.forEach(e => { changeHeightMode( e ); });
    let onChangeHeightMode = function(event) {
        changeHeightMode( event.target );
    }
    height_mode_radio.forEach(e => {
        e.addEventListener("change", onChangeHeightMode );
    });

    // ========================================================
    // イベント：保存時範囲変更
    // ========================================================
    save_cg4000_chk.addEventListener("change",
    function(ev) {
        save_cg4000 = ev.target.checked;
    });
    save_cg4000 = save_cg4000_chk.checked;

    // ========================================================
    // イベント：自動保存モード変更
    // ========================================================
    let onChangeQuickSaveMode = function(event) {
        const e = event.target;
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
    
    // ========================================================
    // パレット反映スイッチ
    // ========================================================
    palette_use_chk.addEventListener("change", function() {
        palette_use_chk2.checked = 
        palette_use = palette_use_chk.checked;
        vdp.update();
        vdp.draw();
        displayCurrentFilename();
    });
    palette_use_chk2.addEventListener("change", function() {
        palette_use_chk.checked = 
        palette_use = palette_use_chk2.checked;
        vdp.update();
        vdp.draw();
        displayCurrentFilename();
    });
    palette_use_chk2.checked = 
    palette_use = palette_use_chk.checked;

    // ========================================================
    // イベント：スプライト制限変更
    // ========================================================
    function changeSpriteLimitMode(e) { 
        if (e.checked) {
            sprite_limit_mode = parseInt(e.value);
            vdp.update();
            vdp.draw();
        }
    }
    sprite_limit_mode_radio.forEach(e => { changeSpriteLimitMode(e); });
    let onChangeSpriteLimitMode = function(event) {
        changeSpriteLimitMode( event.target );
    }
    sprite_limit_mode_radio.forEach(e => {
        e.addEventListener("change", onChangeSpriteLimitMode );
    });

    // ========================================================
    // イベント：VRAM接続方式
    // ========================================================
    vram_interleave_chk.addEventListener('change', 
    function(event) {
        vram_interleave = pal_not_use_vram_chk.checked;
    });
    vram_interleave = vram_interleave_chk.checked;
    
    // ========================================================
    // イベント：カラーパレットをVRAMから読み込まない
    // ========================================================
    pal_not_use_vram_chk.addEventListener('change', 
    function(event) {
        pal_not_use_vram = pal_not_use_vram_chk.checked;
    });
    pal_not_use_vram = pal_not_use_vram_chk.checked;
    
    // ========================================================
    // イベント：カラーパレット未使用時にTMS9918Aの色にする
    // ========================================================
    pal_use_tms9918_chk.addEventListener('change', 
    function(event) {
        pal_use_tms9918 = pal_use_tms9918_chk.checked;
        vdp.updateDefaultColorPalette();
        vdp.update();
        vdp.draw();
        displayCurrentFilename();
    });
    pal_use_tms9918 = pal_use_tms9918_chk.checked;

    // ========================================================
    // イベント：グレースケールで表示
    // ========================================================
    pal_grayscale_chk.addEventListener('change', 
    function(event) {
        use_grayscale = pal_grayscale_chk.checked;
        vdp.update();
        vdp.draw();
    });
    use_grayscale = pal_grayscale_chk.checked;

    // ========================================================
    // イベント：スプライト16x16
    // ========================================================
    sel_sprite_mode.addEventListener('change', 
    function(event) {
        const e = event.target;
        let m = e.selectedIndex;
        vdp.sprite16x16 = (m >> 1) & 1;
        vdp.sprite_double = m & 1;
        vdp.update();
        vdp.draw();
        displaySpriteInfo();
    });
    {
        let m = sel_sprite_mode.selectedIndex;
        vdp.sprite16x16 = (m >> 1) & 1;
        vdp.sprite_double = m & 1;
    }
    
    // ========================================================
    // イベント：キャラクタジェネレータテーブル
    // ========================================================
    let onChangePatNam = function(e) {
        let p = sel_patnam_page;
        let o = sel_patnam_ofs;
        if (p.disabled || o.disabled) return;
        let pg = parseInt(p.options[p.selectedIndex].value);
        let of = parseInt(o.options[o.selectedIndex].value);
        vdp.setPatternNameTable( pg * vdp.mode_info.block_size + of );
        vdp.update();
        vdp.draw();
        displayTableBaseInfo();
    }
    sel_patnam_page.addEventListener('change', onChangePatNam );
    sel_patnam_ofs .addEventListener('change', onChangePatNam );

    let onChangePatGen = function(e) {
        let p = sel_patgen_page;
        let o = sel_patgen_ofs;
        if (p.disabled || o.disabled) return;
        let pg = parseInt(p.options[p.selectedIndex].value);
        let of = parseInt(o.options[o.selectedIndex].value);
        vdp.setPatternGeneratorTable( pg * vdp.mode_info.block_size + of );
        vdp.update();
        vdp.draw();
        displayTableBaseInfo();
    }
    sel_patgen_page.addEventListener('change', onChangePatGen );
    sel_patgen_ofs .addEventListener('change', onChangePatGen );

    let onChangePatCol = function(e) {
        if (vdp.base.patcol < 0) return;
        let p = sel_patcol_page;
        let o = sel_patcol_ofs;
        if (p.disabled || o.disabled) return;
        let pg = parseInt(p.options[p.selectedIndex].value);
        let of = parseInt(o.options[o.selectedIndex].value);
        vdp.setPatternColorTable( pg * vdp.mode_info.block_size + of );
        vdp.update();
        vdp.draw();
        displayTableBaseInfo();
    }
    sel_patcol_page.addEventListener('change', onChangePatCol );
    sel_patcol_ofs .addEventListener('change', onChangePatCol );

    patgen_chk.addEventListener("change",
    function(ev) {
        let e = ev.target;
        nouse_patgen = !e.checked;
        if (!e.checked) {
            patcol_chk.checked = true;  // どちらかは必ずチェック
            nouse_patcol = false;
        }
        vdp.update();
        vdp.draw();
    });
    patcol_chk.addEventListener("change",
    function(ev) {
        let e = ev.target;
        nouse_patcol = !e.checked;
        if (!e.checked) {
            patgen_chk.checked = true;  // どちらかは必ずチェック
            nouse_patgen = false;
        }
        vdp.update();
        vdp.draw();
    });

    // ========================================================
    // イベント：スプライトテーブル
    // ========================================================
    let onChangeSprAtr = function(e) {
        let p = sel_spratr_page;
        let o = sel_spratr_ofs;
        if (p.disabled || o.disabled) return;
        let pg = parseInt(p.options[p.selectedIndex].value);
        let of = parseInt(o.options[o.selectedIndex].value);
        vdp.setSpriteAttributeTable( pg * vdp.mode_info.block_size + of );
        vdp.update();
        vdp.draw();
        displayTableBaseInfo();
    }
    sel_spratr_page.addEventListener('change', onChangeSprAtr );
    sel_spratr_ofs .addEventListener('change', onChangeSprAtr );

    let onChangeSprPat = function(e) {
        let p = sel_sprpat_page;
        let o = sel_sprpat_ofs;
        if (p.disabled || o.disabled) return;
        let pg = parseInt(p.options[p.selectedIndex].value);
        let of = parseInt(o.options[o.selectedIndex].value);
        vdp.setSpritePatternTable( pg * vdp.mode_info.block_size + of );
        vdp.update();
        vdp.draw();
        displayTableBaseInfo();
    }
    sel_sprpat_page.addEventListener('change', onChangeSprPat );
    sel_sprpat_ofs .addEventListener('change', onChangeSprPat );

    // ========================================================
    // イベント：スクロール
    // ========================================================
    let DragInfo = class {
        start = { x: 0, y: 0, v: 0 };
        rel   = { x: 0, y: 0, v: 0 };
        drag  = false;
        constructor() {}
        start_drag( x, y, v ) {
            this.start = { x: x, y: y, v: v };
            this.rel   = { x: 0, y: 0, v: 0 };
            this.drag  = true;
        }
        move_drag( x, y ) {
            this.rel.x = x - this.start.x;
            this.rel.y = y - this.start.y;
        }
    }
    // --------------------------------------------------------
    // 縦スクロール
    // --------------------------------------------------------
    //let vscroll_controll = canvas_area;
    let vscroll_controll = detail_vscroll;
    let vscroll_drag =  new DragInfo();
    function onMouseDownVScroll(e) {
        // 選択解除
        //if (window.getSelection) window.getSelection().removeAllRanges();
        // 全体を選択不能にする
        document.getElementById('main').style['user-select'] = 'none';
        let rect = vscroll_controll.getBoundingClientRect();
        vscroll_drag.start_drag( e.clientX - rect.left, e.clientY - rect.top, vdp.vscroll);
    }
    function vscroll_drag_move( end ) {
        if (vscroll_drag.drag) {
        if (vscroll_drag.rel.y || !end) {
                vdp.vscroll = (vscroll_drag.start.v - vscroll_drag.rel.y / 2) & 255;
            } else {
                vdp.vscroll = 0;
            }
            vdp.draw();
            displayScrollInfo();
        }
    }
    function onMouseMoveVScroll(e) {
        // 選択解除
        //if (window.getSelection) window.getSelection().removeAllRanges();
        let rect = vscroll_controll.getBoundingClientRect();
        vscroll_drag.move_drag( e.clientX - rect.left, e.clientY - rect.top );
        vscroll_drag_move( false );
    }
    function onMouseUpVScroll(e) {
        vscroll_drag_move( true );
        if (vscroll_drag.drag) {
            // 選択解除
            //if (window.getSelection) window.getSelection().removeAllRanges();
            // 全体を選択可能に戻す
            document.getElementById('main').style['user-select'] = 'auto';
        }
        vscroll_drag.drag = false;
    }
    vscroll_controll.addEventListener("mousedown", onMouseDownVScroll);
    window.addEventListener("mousemove", onMouseMoveVScroll);
    window.addEventListener("mouseup", onMouseUpVScroll);
    // --------------------------------------------------------
    // 横スクロール
    // --------------------------------------------------------
    //let hscroll_controll = canvas_area;
    let hscroll_controll = detail_hscroll;
    let hscroll_drag = new DragInfo();
    function onMouseDownHScroll(e) {
        // 全体を選択不能にする
        document.getElementById('main').style['user-select'] = 'none';
        let rect = hscroll_controll.getBoundingClientRect();
        hscroll_drag.start_drag( e.pageX - rect.left, e.pageY - rect.top, vdp.hscroll);
    }
    function hscroll_drag_move( end ) {
        if (hscroll_drag.drag) {
            if (hscroll_drag.rel.x || !end) {
                vdp.hscroll = (hscroll_drag.start.v - hscroll_drag.rel.x / 2) & 511;
            } else {
                vdp.hscroll = 0;
            }
            vdp.pre_render();
            vdp.draw();
            displayScrollInfo();
        }
    }
    function onMouseMoveHScroll(e) {
        let rect = hscroll_controll.getBoundingClientRect();
        hscroll_drag.move_drag( e.pageX - rect.left, e.pageY - rect.top );
        hscroll_drag_move( false );
    }
    function onMouseUpHScroll(e) {
        hscroll_drag_move( true );
        if (hscroll_drag.drag) {
            // 全体を選択可能に戻す
            document.getElementById('main').style['user-select'] = 'auto';
        }
        hscroll_drag.drag = false;
    }
    hscroll_controll.addEventListener("mousedown", onMouseDownHScroll);
    window.addEventListener("mousemove", onMouseMoveHScroll);
    window.addEventListener("mouseup", onMouseUpHScroll);
    //detail_hscroll.style.display = "none"; // 未実装なので一旦非表示
    // --------------------------------------------------------
    // 横スクロール マスク
    // --------------------------------------------------------
    hscroll_mask_chk.addEventListener("change",
    function(e) {
        vdp.r25_msk = e.target.checked ? 1 : 0;
        vdp.update();
        vdp.draw();
        displayScrollInfo();
    });
    vdp.r25_msk = hscroll_mask_chk.checked;
    // --------------------------------------------------------
    // 横スクロール 2ページ
    // --------------------------------------------------------
    hscroll_2page_chk.addEventListener("change",
    function(e) {
        vdp.r25_sp2 = (e.target.checked && vdp.screen_no) ? 1 : 0;
        if (vdp.screen_no) {
            vdp.setPage( (vdp.disp_page & ~1) | vdp.r25_sp2 | vdp.interlace_mode);
        }
        vdp.update();
        vdp.draw();
        displayCurrentFilename();
    });
    vdp.r25_sp2 = hscroll_2page_chk.checked;

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
    file_open_button.addEventListener("change",
    function(e) {
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
    // --------------------------------------------------------
    // 設定ファイル
    // --------------------------------------------------------
    config_save.addEventListener("click", e => { saveConfig(); });
    // --------------------------------------------------------
    // パレットファイル
    // --------------------------------------------------------
    pal_save.addEventListener("click", e => { savePalette(); });
    // ========================================================
    function savePage(file, page, commpress, with_pal)
    {
        if (bmp_file.size && bmp_file.name.length) {
            let page_file = LogFile(bmp_file);
            page_file.header = new BinHeader( bmp_file.header );
            let ext = getExt(page_file.name);
            let base = getBasename(page_file.name);
            page_file.name = base + '_page' + page + '.' + ext;
            saveImage(page_file, page, commpress, with_pal);
        } else if (file != null) {
            saveImage(file, page, commpress, with_pal);
        }
    }
    // --------------------------------------------------------
    // all bsave
    // --------------------------------------------------------
    all_save_bsave.addEventListener("click",
    function(e) { saveAll( 0, 1 ); });
    all_save_bsave_np.addEventListener("click",
    function(e) { saveAll( 0, 0 ); });
    all_save_gsrle.addEventListener("click",
    function(e) { saveAll( 1, 0 ); });
    // --------------------------------------------------------
    // page 0 bsave
    // --------------------------------------------------------
    page0_save_bsave.addEventListener("click",
    function(e) { savePage( main_file, 0, 0, 1 ); });
    page0_save_bsave_np.addEventListener("click",
    function(e) { savePage( main_file, 0, 0, 0 ); });
    page0_save_gsrle.addEventListener("click",
    function(e) { savePage( main_file, 0, 1, 0 ); });
    // --------------------------------------------------------
    // page 1 bsave
    // --------------------------------------------------------
    page1_save_bsave.addEventListener("click",
    function(e) { savePage( sub_file, 1, 0, 1 ); });
    page1_save_bsave_np.addEventListener("click",
    function(e) { savePage( sub_file, 1, 0, 0 ); });
    page1_save_gsrle.addEventListener("click",
    function(e) { savePage( sub_file, 1, 1, 0 ); });
    // --------------------------------------------------------
    // page 2 bsave
    // --------------------------------------------------------
    page2_save_bsave.addEventListener("click",
    function(e) { savePage( null, 2, 0, 1 ); });
    page2_save_bsave_np.addEventListener("click",
    function(e) { savePage( null, 2, 0, 0 ); });
    page2_save_gsrle.addEventListener("click",
    function(e) { savePage( null, 2, 1, 0 ); });
    // --------------------------------------------------------
    // page 3 bsave
    // --------------------------------------------------------
    page3_save_bsave.addEventListener("click",
    function(e) { savePage( null, 3, 0, 1 ); });
    page3_save_bsave_np.addEventListener("click",
    function(e) { savePage( null, 3, 0, 0 ); });
    page3_save_gsrle.addEventListener("click",
    function(e) { savePage( null, 3, 1, 0 ); });
    
    // ========================================================
    // TEST
    // ========================================================
    // --------------------------------------------------------
    // test button1 明るい色側をビット1に変更する
    // --------------------------------------------------------
    let test_button1 = document.getElementById('test_button1');
    test_button1.addEventListener('click',
    function(e) {
        vdp.modifyPatternByBrightnessOrder();
        vdp.update();
        vdp.draw();
    });

    // --------------------------------------------------------
    // test button2 パレットクリックでグレースケール切替
    // --------------------------------------------------------
    palette_area.addEventListener('mousedown',
    function(e) {
        // 全体を選択不能にする
        document.getElementById('main').style['user-select'] = 'none';
        use_grayscale_tmp = true;
        vdp.update();
        vdp.draw();
    });
    window.addEventListener('mouseup',
    function(e) {
        if (use_grayscale_tmp) {
            // 全体を選択可能に戻す
            document.getElementById('main').style['user-select'] = 'auto';
            use_grayscale_tmp = false;
            vdp.update();
            vdp.draw();
        }
    });

    // --------------------------------------------------------
    // スプライト 透明背景の色変更
    // --------------------------------------------------------
    transparent_bg_chk.addEventListener("change",
    function(e) {
        sprgen_bg_type = e.target.checked ? 1 : 0;
        setTransparentBg(canvas_sprgen, sprgen_bg_type);
    });
    sprgen_bg_type = transparent_bg_chk.checked ? 1 : 0;
    setTransparentBg(canvas_sprgen, sprgen_bg_type);

    let sprgen_canvas_mousedown = false;
    canvas_sprgen.addEventListener('mousedown',
    function(e) {
        // 全体を選択不能にする
        document.getElementById('main').style['user-select'] = 'none';
        sprgen_canvas_mousedown = true;
        setTransparentBg(canvas_sprgen, 1 - sprgen_bg_type);
    });
    window.addEventListener('mouseup',
    function(e) {
        if (sprgen_canvas_mousedown) {
            // 全体を選択可能に戻す
            document.getElementById('main').style['user-select'] = 'auto';
            sprgen_canvas_mousedown = false;
            setTransparentBg(canvas_sprgen, sprgen_bg_type);
        }
    });


    // ========================================================
    // 実行
    // ========================================================
    ///* test
    vdp.changeScreen(2);
    vdp.sprite16x16 = 1;
    //*/

	vdp.updateDefaultColorPalette();
    vdp.cls();
    vdp.setColor();
    vdp.print('Hello World.');
    vdp.setColor(10);
    vdp.print('MSX Graphics viewer です。');
    vdp.setColor(2);
    vdp.print('こんにちは。');
    vdp.setColor(7);
    vdp.print('ここへファイルをドロップしてください。');

    vdp.update();
    vdp.draw();
    displayCurrentFilename();

//    saveConfig
});

