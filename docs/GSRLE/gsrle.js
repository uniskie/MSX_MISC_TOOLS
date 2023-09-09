const toString = Object.prototype.toString;

// ========================================================
// グローバル変数
// ========================================================

// 初期画面モード
const default_screen_no = 1;

let default_log_hml = ''

// 初回（自動でアコーディオンタブを閉じる）
let isFirst = true;

// ドラッグアンドドロップ受付状態
let drop_avilable = true;

// パレット反映スイッチ
let palette_use = true;

// 自動保存モード
let quick_save_mode = 'none';
const quick_save_mode_value = 
 ['none', 'bsave_full', 'bsave_mini', 'gsrle_save'];
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

//================================================
// クランプ
//================================================
function clamp( n, min, max ) {
    n = Math.max( min, Math.min( n, max ) );
    return n;
}

//================================================
// 指定値単位になるビットマスクを作成
//================================================
function bitmask32( d ) 
{
    return 0xffffffff - (d - 1);
}

//================================================
// 桁サプレス
//================================================
function zerosup( n, k ) {
    let ns = Math.abs(n).toString(16);
    if (ns.length < k) {
        ns = `0`.repeat(k - ns.length) + ns;
    }
    if (n < 0) return '-' + ns;
    return ns;
}

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
        detail_page1.style.display ="none";
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

    displayCurrentScreenMode();
}
// ========================================================
// 現在の画面モード情報
// ========================================================
function displayCurrentScreenMode() {

    if (vdp.base.patcol < 0) {
        detail_chrgen_spec.innerText = 
        `[name:0x${zerosup(vdp.base.patnam, 5)}] `+
        `[gen:0x${zerosup(vdp.base.patgen, 5)}]`;
    } else {
        detail_chrgen_spec.innerText = 
        `[name:0x${zerosup(vdp.base.patnam, 5)}] `+
        `[gen:0x${zerosup(vdp.base.patgen, 5)}] `+
        `[color:0x${zerosup(vdp.base.patcol, 5)}]`;
    }

    if (vdp.base.sprcol < 0) {
        detail_sprgen_spec.innerText = 
        `[atr:0x${zerosup(vdp.base.spratr, 5)}] `+
        `[pat:0x${zerosup(vdp.base.sprpat, 5)}]`;
    } else {
        detail_sprgen_spec.innerText = 
        `[atr:0x${zerosup(vdp.base.spratr, 5)}] `+
        `[pat:0x${zerosup(vdp.base.sprpat, 5)}] `+
        `[color:0x${zerosup(vdp.base.sprcol, 5)}]`;
    }

    // スプライト無効/有効
    chk_sprite_use.checked = !vdp.sprite_disable;
    if (vdp.sprite_disable) {
        label_sprite_use.innerText = 'Sprite Off';
    } else {
        label_sprite_use.innerText = 'Sprite On';
    }

    // スプライト設定
    sel_sprite_mode.selectedIndex =
        (vdp.sprite16x16 << 1) | vdp.sprite_double;

    // 画面設定表示
    {
        sel_screen_no.selectedIndex = vdp.screen_no;
        chk_screen_interlace.checked = vdp.interlace_mode;
        if (vdp.screen_no < 5) {
            //sel_disp_page.disabled = true;
            let page_size = vdp.mode_info.page_size;
            let page = Math.floor(vdp.base.patnam / page_size);
            if (page != Math.floor(vdp.base.patgen / page_size)) page = -1;
            if (0 <= vdp.base.patcol) {
                if (page != Math.floor(vdp.base.patcol / page_size)) page = -1;
            }
            sel_disp_page.selectedIndex = page;
            //sel_disp_page.disabled = false;
        } else {
            sel_disp_page.selectedIndex = vdp.disp_page;
        }
        detail_screen_mode_name.textContent = `[${vdp.mode_info.name}]`;
        detail_screen_width.textContent = `[WIDTH:${vdp.width}]`;
        detail_screen_height.textContent = `[HEIGHT:${vdp.height}]`;
        if (vdp.interlace_mode) detail_interlace.textContent = '[Interlaced]';
        else                    detail_interlace.textContent = '[Non-Interlace]';
        if (vdp.sprite_disable) detail_sprite_on.textContent = '[SPRITE OFF]';
        else 
        if (vdp.sprite_double) {
            if (vdp.sprite16x16 )   detail_sprite_on.textContent = '[SPRITE 16x16 x2]';
            else                    detail_sprite_on.textContent = '[SPRITE 8x8 x2]';
        } else {
            if (vdp.sprite16x16 )   detail_sprite_on.textContent = '[SPRITE 16x16]';
            else                    detail_sprite_on.textContent = '[SPRITE 8x8]';
        }

        let page_size = vdp.mode_info.page_size;
        let page_mask = page_size - 1;
        selSelectOption( sel_patnam_ofs , vdp.base.patnam & page_mask );
        selSelectOption( sel_patnam_page, Math.floor(vdp.base.patnam / page_size));
        selSelectOption( sel_patgen_ofs ,            vdp.base.patgen & page_mask );
        selSelectOption( sel_patgen_page, Math.floor(vdp.base.patgen / page_size));
        if (vdp.base.patcol < 0) {
            sel_patcol_ofs.selectedIndex = -1;
            sel_patcol_page.selectedIndex = -1;
        } else {
            selSelectOption( sel_patcol_ofs ,            vdp.base.patcol & page_mask );
            selSelectOption( sel_patcol_page, Math.floor(vdp.base.patcol / page_size));
        }
        selSelectOption( sel_spratr_ofs ,            vdp.base.spratr & page_mask );
        selSelectOption( sel_spratr_page, Math.floor(vdp.base.spratr / page_size));
        selSelectOption( sel_sprpat_ofs ,            vdp.base.sprpat & page_mask );
        selSelectOption( sel_sprpat_page, Math.floor(vdp.base.sprpat / page_size));
    }
}

function setAttributeTableList()
{
    if (!vdp) return;
    if (!sel_spratr_page) return;

    function addLists( t, pe, e, funcidx, funcn, def_v ) {
        let page = parseInt(def_v / vdp.mode_info.page_size);
        let def = def_v - page * vdp.mode_info.page_size;

        removeAllSelectOption( pe );
        removeAllSelectOption( e );

        for (let n = 0; n < vdp.max_page; ++n ) {
            addSelectOption( pe, `Page ${n}`, n );
        }

        let selectedIndex = -1;
        let a = -1;
        for (let n = 0;; ++n) {
            a = funcidx( n );
            if (a < 0)break;
            if (vdp.mode_info.page_size <= a) break;
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

    //================================================
    // CHARACTER GENERATOR TABLE
    //================================================
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
    
    //================================================
    // SPRITE TABLE
    //================================================
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

//================================================
// ドロップダウンリスト 要素：クリア
//================================================
function removeAllSelectOption( e ) {
    while (e.options.length) {
        e.remove(0);
    }
}
//================================================
// ドロップダウンリスト 要素：追加
//================================================
function addSelectOption( e, t, v ) {
    let o = new Option( t, v );
    e.options[ e.options.length ] = o;
    return o;
}
//==========ｌ=====================================
// ドロップダウンリスト 要素：指定値を選択
//================================================
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

    {ext:'.BMP', screen_no:-1, interlace:-1, page:-1, type:2, bsave:'.SCR', gs:'.GSR'},	// RAWイメージ OpenMSX vram2bmp の非圧縮BMP
    {ext:'.SCR', screen_no:-1, interlace:-1, page:-1, type:2, bsave:'.SCR', gs:'.GSR'},	// RAWイメージ
    {ext:'.GSR', screen_no:-1, interlace:-1, page:-1, type:2, bsave:'.SCR', gs:'.GSR'},	// RAWイメージ

    // 仮対応：スクリーン0、1
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
// カラーパレット
//================================================
class PaletteEntry {
    [Symbol.toStringTag] = 'PaletteEntry';
    /*
        MSX palette 777
        16bit - 0grb
        8bit - rb, 0g
    */
    constructor( r, g, b, a ) {
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
    setRgb888(r,g,b) {
        this.r = clamp(Math.floor((r + 4) * 7 / 255), 0, 7);
        this.g = clamp(Math.floor((g + 4) * 7 / 255), 0, 7);
        this.b = clamp(Math.floor((b + 4) * 7 / 255), 0, 7);
    }
    get rgba() {
        return Uint8Array.from([
            clamp(Math.floor(this.r * 255 / 7), 0, 255),
            clamp(Math.floor(this.g * 255 / 7), 0, 255),
            clamp(Math.floor(this.b * 255 / 7), 0, 255),
            0xff]);
    }
    get rgb_string() {
        var r = this.rgba;
        //return 'rgb('+r[0]+','+r[1]+','+r[2]+')';
        return `rgb( ${r[0]}, ${r[1]}, ${r[2]} )`;
    }
};
class Palette {
    [Symbol.toStringTag] = 'PaletteEntry';
    constructor( entry_count, d ) {
        const p = this;
        p.color = new Array( entry_count );
        p.rgba = new Array( entry_count );
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
            d[idx + 0] = p.color[i].rgb777 & 255;
            d[idx + 1] = (p.color[i].rgb777 >> 8) & 255;
        }
        return d;
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
	static get aspect_ratio2() { return 1.177; } // openMSX 3x:904 2x:603 1x:301

    static get screen_width () { return 512; }
	static get screen_height() { return 424; }

	static get vram_size() { return 0x20000; }	// 128 * 1024;

    static get palette_count() { return 16; }

    //------------------------------------------------
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
    // 画面モード別 アドレス指定可能単位
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
    	let info = { 
              ...VDP.screen_mode_spec1[no]
             , ...VDP.screen_mode_spec2[no]
             , ...VDP.screen_mode_spec3[no] 
             , ...VDP.screen_mode_spec4[no] 
        };

        // VRAMパレットエントリエンド
        info.palend = info.paltbl + 32 -1;

        info.sPal = Math.max(info.s212, info.palend);
        return info;
    }

    //------------------------
    // コンストラクタ
    //------------------------
	constructor( cs ) {
        const p = this;

        //------------------------
        // vram area
        p.vram = new Uint8Array( VDP.vram_size );

        //------------------------
        // 表示page
        p.disp_page = 0;

        //------------------------
        // お遊び
        p.draw_page = 0;    // お遊び用
        p.x = 0;
        p.y = 0;
        p.color = 15;


        //------------------------
        // default color palette
        p.pal_def = new Palette( VDP.palette_count, VDP.msx2pal );

        // current color palette
        p.palette = new Palette( VDP.palette_count, VDP.msx2pal );
        
        //------------------------
        // screen8 color palette
        p.pal256 = new Palette( 256 );
        p.pal8spr = new Palette( VDP.palette_count, VDP.sc8spr_pal );

        //------------------------
        // canvas
        p.cs = {
            canvas:         null,
            pal_canvas:     null,
            page_canvas:    [null, null, null, null],
            patgen_canvas:  null,
            sprgen_canvas:  null
        };
        p.offscreen = [null, null, null]; // disp, work, spr
        p.imgData   = null;
        p.sprData   = null;

        if (cs !== undefined) {
            if (cs.canvas !== undefined)        p.cs.canvas = cs.canvas;
            if (cs.pal_canvas !== undefined)    p.cs.pal_canvas = cs.pal_canvas;
            if (cs.page_canvas !== undefined) {
                p.cs.page_canvas[0] = cs.page_canvas[0];
                p.cs.page_canvas[1] = cs.page_canvas[1];
                p.cs.page_canvas[2] = cs.page_canvas[2];
                p.cs.page_canvas[3] = cs.page_canvas[3];
            }
            if (cs.patgen_canvas !== undefined)    p.cs.patgen_canvas = cs.patgen_canvas;
            if (cs.sprgen_canvas !== undefined)    p.cs.sprgen_canvas = cs.sprgen_canvas;
        }

        //------------------------
        // screen 情報
        p.screen_no = default_screen_no;
        p.mode_info = VDP.getScreenModeSetting( p.screen_no );
        p.width     = p.mode_info.width;
        p.height    = p.mode_info.height;
        p.scan_line_count = 256;
        p.max_page  = p.vram.length / p.mode_info.page_size;
        p.canvas_max_page = Math.min(p.cs.page_canvas.length, p.max_page);
        p.force_height = 0;
        p.auto_detect_height = 0;
        p.img_width  = p.width;
        p.img_height = p.height;
        p.interlace_mode = 0;
        p.disp_page = 0;
        p.aspect_ratio = 1.177;
        p.base = {
            patnam: p.mode_info.patnam,
            patgen: p.mode_info.patgen,
            patcol: p.mode_info.patcol,
            spratr: p.mode_info.spratr,
            sprpat: p.mode_info.sprpat,
            sprcol: p.mode_info.sprcol,
        };

        //------------------------
        // スプライト
        p.spr_scan_width = 256;
        p.spr_scan_height = 256;

        p.sprite16x16 = 0;
        p.sprite_double = 0;

        p.changeScreen( p.screen_no , p.mode_info.txw, p.interlace_mode );
        p.cls();
    }

    setPage( page ) {
        let p = this;
        p.disp_page = Math.max(0, Math.min( page, p.max_page - 1));
        if (p.screen_no < 5) {
            let page_add = p.disp_page * p.mode_info.page_size;
            let page_mask = (p.mode_info.page_size - 1);
            p.setPatternNameTable( (p.base.patnam & page_mask) + page_add );
            p.setPatternGeneratorTable( (p.base.patgen & page_mask) + page_add );
            if (0 <= p.base.patcol) {
                p.setPatternColorTable( (p.base.patcol & page_mask) + page_add );
            }
        }
        return p.disp_page;
    }

    //------------------------
    // ベースアドレス設定
    //------------------------
    setSpriteAttributeTable( n ) {
        const p = this;
        if (n === undefined) {
            p.base.spratr = p.mode_info.spratr;
        } else 
        if (p.screen_no < 4) {
            // SPRITE mode 1
            p.base.spratr = n & bitmask32(0x80);
            p.base.sprcol = -1;
        } else {
            n &= bitmask32(0x400);
            p.base.spratr = n + 0x200;
            p.base.sprcol = n;
        }
        return p.base.spratr;
    }
    setSpriteAttributeTableIdx( n ) {
        const p = this;
        if (n === undefined) {
            p.base.spratr = p.mode_info.spratr;
        } else 
        if (p.screen_no < 4) {
            // SPRITE mode 1
            p.base.spratr = n * 0x80;
            p.base.sprcol = -1;
        } else {
            p.base.spratr = n * 0x400 + 0x200;
            p.base.sprcol = n * 0x400;
        }
        return p.base.spratr;
    }
    setSpritePatternTable( n ) {
        const p = this;
        if (n === undefined) {
            p.base.sprpat = p.mode_info.sprpat;
        } else {
            p.base.sprpat = n & bitmask32(0x800);
        }
        return p.base.sprpat;
    }
    setSpritePatternTableIdx( n ) {
        const p = this;
        if (n === undefined) {
            p.base.sprpat = p.mode_info.sprpat;
        } else {
            p.base.sprpat = n * 0x800;
        }
        return p.base.sprpat;
    }
    setPatternNameTable( n ) {
        const p = this;
        if (n === undefined) {
            p.base.patnam = p.mode_info.patnam;
        } else {
            p.base.patnam = n & bitmask32(p.mode_info.u_patnam);
        }
        return p.base.patnam;
    }
    setPatternNameTableIdx( n ) {
        const p = this;
        if (n === undefined) {
            p.base.patnam = p.mode_info.patnam;
        } else {
            p.base.patnam = p.mode_info.u_patnam * n;
        }
        return p.base.patnam;
    }
    setPatternGeneratorTable( n ) {
        const p = this;
        if (n === undefined) {
            p.base.patgen = p.mode_info.patgen;
        } else {
            p.base.patgen = n & bitmask32(p.mode_info.u_patgen);
        }
        return p.base.patgen;
    }
    setPatternGeneratorTableIdx( n ) {
        const p = this;
        if (n === undefined) {
            p.base.patgen = p.mode_info.patgen;
        } else {
            p.base.patgen = p.mode_info.u_patgen * n;
        }
        return p.base.patgen;
    }
    setPatternColorTable( n ) {
        const p = this;
        if (n === undefined) {
            p.base.patcol = p.mode_info.patcol;
        } else {
            p.base.patcol = n & bitmask32(p.mode_info.u_patgen);
        }
        return p.base.patcol;
    }
    setPatternColorTableIdx( n ) {
        const p = this;
        if (n === undefined) {
            p.base.patcol = p.mode_info.patcol;
        } else {
            p.base.patcol = p.mode_info.u_patgen * n;
        }
        return p.base.patcol;
    }


    //------------------------
    // カラーパレット初期化
    //------------------------
    resetPalette() { 
        this.palette.setPalette( this.pal_def.color ); 
    }
    //------------------------
    // カラーパレットを設定
    //------------------------
    restorePalette( d ) {
        const p = this;
        if (d === undefined) {
            // VRAMから読み込む
            p.palette.setPalette( p.vram.subarray( p.mode_info.paltbl, p.mode_info.paltbl + 32  ) );
        } else {
            // 指定データから読み込む
            p.palette.setPalette( d );
        }
    }
    //------------------------
    // カラーパレットを返す
    //------------------------
    getPalTbl() {
        return this.palette.getPalTbl();
    }

    //------------------------
    // デフォルトカラーパレット更新
    //------------------------
    updateDefaultColorPalette() {
        const p = this;
        if ((p.screen_no < 4) && (pal_use_tms9918.checked)) {
            p.pal_def = new Palette( VDP.palette_count, VDP.msx1fpal );
            p.pal_def.setRgba( VDP.tms9918pal8888 ); // 8888精度の色で表示
        } else {
            p.pal_def = new Palette( VDP.palette_count, VDP.msx2pal );
        }
    }

    //------------------------
    // 画面モード変更
    //------------------------
    changeScreen( screen_no, txw, interlace_mode, force_height, reset_base ) {
        const p = this;

        let old_screen_no = p.screen_no;

        p.screen_no = screen_no;
        p.mode_info = VDP.getScreenModeSetting( screen_no, txw );
        p.width  = p.mode_info.width;
        p.height = p.mode_info.height;
        p.max_page  = p.vram.length / p.mode_info.page_size;
        p.canvas_max_page = Math.min(p.cs.page_canvas.length, p.max_page);

        p.updateDefaultColorPalette();

        if (p.auto_detect_height) {
            p.height = p.auto_detect_height;
        }
        if (force_height === undefined) {
            force_height = p.force_height;
        }
        if (force_height) {
            p.height = force_height;
        }

        if (p.screen_no < 5) {
            // SCREEN0～4は仕様が分からないのでインターレースモードは禁止
            p.interlace_mode = 0;
        } else {
            if (interlace_mode === undefined ) {
                interlace_mode = 0;
            }
            if (screen_no != old_screen_no)
            {
                p.setPage( 0 );
            }
            if (p.interlace_mode != interlace_mode) {
                p.interlace_mode = interlace_mode
                // ページはインターレース（＋フリップ）時では奇数に指定
                p.setPage( (p.disp_page & 254) + p.interlace_mode);
            }
        }

        p.img_width  = p.width;
        p.img_height = p.height * (p.interlace_mode + 1);

        // base address
        reset_base |= false;
        if (reset_base || (screen_no != old_screen_no)) {
            p.base.patnam = p.mode_info.patnam;
            p.base.patgen = p.mode_info.patgen;
            p.base.patcol = p.mode_info.patcol;
            p.base.spratr = p.mode_info.spratr;
            p.base.sprpat = p.mode_info.sprpat;
            p.base.sprcol = p.mode_info.sprcol;
        }

        if (p.cs.canvas) {
    		p.initCanvas();
        }

        setAttributeTableList();
    }

    //------------------------
    // 描画キャンバス初期化
    //------------------------
    initCanvas( cs ) {
    	const p = this;

        if (cs !== undefined) {
            if (cs.canvas !== undefined)        p.cs.canvas = cs.canvas;
            if (cs.pal_canvas !== undefined)    p.cs.pal_canvas = cs.pal_canvas;
            if (cs.page_canvas !== undefined) {
                p.cs.page_canvas[0] = cs.page_canvas[0];
                p.cs.page_canvas[1] = cs.page_canvas[1];
                p.cs.page_canvas[2] = cs.page_canvas[2];
                p.cs.page_canvas[3] = cs.page_canvas[3];
            }
            if (cs.patgen_canvas !== undefined)    p.cs.patgen_canvas = cs.patgen_canvas;
            if (cs.sprgen_canvas !== undefined)    p.cs.sprgen_canvas = cs.sprgen_canvas;
        }

        if (!p.cs.canvas) {
            console.log('initCanvas - p.cs.canvas is null.');
            return;
        }

         // イメージバッファ作成
         p.offscreen[0] = new OffscreenCanvas(p.img_width, p.img_height);//最終出力先
         p.offscreen[1] = new OffscreenCanvas(p.width, p.scan_line_count * p.canvas_max_page);   // ページ分
         p.offscreen[2] = new OffscreenCanvas(p.spr_scan_width, p.spr_scan_height + 64);           // 1画面 + パターンリスト
        var ctx = p.offscreen[1].getContext('2d');
        p.imgData = ctx.createImageData(p.offscreen[1].width, p.offscreen[1].height);
        p.sprData = ctx.createImageData(p.offscreen[2].width, p.offscreen[2].height);
    }

    //------------------------
    // VRAMクリア
    //------------------------
    cls( resetPalette ) {
        const p = this;

        p.vram.fill( 0 );
        if (resetPalette === undefined) resetPalette = false;
        if (!pal_not_use_vram.checked || resetPalette) {
            p.resetPalette();
            p.vram.set( p.getPalTbl(), p.mode_info.paltbl );
        }

        // お遊び
        p.x = 0;
        p.y = 0;
        p.color = 15;

        // 初期値
        const b = p.vram;
        const tx_size = p.mode_info.txw * p.mode_info.txh;
        let n = p.base.patnam;
        switch (p.screen_no) {
        case 0:
        case 1:
            b.fill(32,p.base.patnam, p.base.patnam + tx_size);
            b.fill(0xf0, p.base.patcol, p.base.patcol + 32);
            b.set( fontdat, p.base.patgen );
            /*
            // test
            if (-1 < p.base.patcol) {
                for (var i=0; i<32; ++i) {
                    b[p.base.patcol + i] = i;
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
            b.fill(0xf0, p.base.patcol, p.base.patcol + tx_size * 8);
            /*
            // test
            for (var i=0; i<tx_size * 8; ++i) {
                b[p.base.patcol + i] = i;
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
                b[p.base.patgen + i] = i;
            }
            //*/
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
        if (p.cs.canvas) {
            // メインキャンバスサイズ
            p.cs.canvas.height = p.height * 2;
            if (p.width <= 256) {
                p.cs.canvas.width = p.width * 2 * p.aspect_ratio;
            } else {
                p.cs.canvas.width = p.width * p.aspect_ratio;
            }
        }
    }

    //------------------------
    // 描画出力
    //------------------------
    draw( disp_mode ) {
    	const p = this;

        //------------------------
        // メインキャンバス
        //------------------------
        if (p.cs.canvas) {
            p.setCanvasSize();

            var ctx = p.cs.canvas.getContext('2d');
            ctx.imageSmoothingEnabled = false;//canvas_smoothing.checked;

            //switch (p.disp_page) {
            //case 0:
            //case 1:
            //    ctx.drawImage( p.offscreen[1], 
            //        0, p.disp_page * p.scan_line_count, p.width, p.height,
            //        0, 0, p.cs.canvas.width, p.cs.canvas.height );
            //    break;
            //default:
                ctx.drawImage( p.offscreen[0],
                    0, 0, p.img_width, p.img_height,
                    0, 0, p.cs.canvas.width, p.cs.canvas.height );
            //    break;
            //}
        }

        //------------------------
        // ページ毎表示キャンバス
        //------------------------
        if (p.cs.page_canvas) {
            var offscreen = p.offscreen[1];

            let height = p.height;

            for (var pg = 0; pg < p.cs.page_canvas.length; ++pg) {
                if (pg >= p.canvas_max_page) break;

                var canvas = p.cs.page_canvas[pg];
                if (pg && (p.screen_no < 5)) {
                    canvas = p.cs.patgen_canvas;
                    //if (3 == p.screen_no) {
                    //    height = 256; // chara_height * chara_count * 4 / txw;
                    //} else
                    if (1 < p.screen_no) {
                        height = 64 * 3; // chara_height * chara_count * chara_gen_count / txw;
                    } else {
                        height = 64;    // chara_height * chara_count  / txw;
                    }
                }
                if (canvas) {
                    canvas.width  = p.cs.canvas.width;
                    canvas.height = height * 2;
                    ctx = canvas.getContext('2d');
                    ctx.imageSmoothingEnabled = false;//canvas_smoothing.checked;
                    ctx.drawImage( offscreen, 
                        0, pg * p.scan_line_count, p.width, height,
                        0, 0, canvas.width, canvas.height );
                }
            }
        }
        //------------------------
        // スプライトジェネレータ
        //------------------------
        if (p.cs.sprgen_canvas) {
            var offscreen = p.offscreen[2];

            // test
            const h = 0;
            const lh = p.spr_scan_height + 64; // 8 * chara_count / txw = 64

            //const h = p.spr_scan_height;
            //const lh = 64; // // 8 * chara_count / txw = 64

            let canvas = p.cs.sprgen_canvas;
            canvas.width  = p.cs.canvas.width;
            canvas.height = lh * 2;
            ctx = canvas.getContext('2d');
            ctx.imageSmoothingEnabled = false;//canvas_smoothing.checked;
            ctx.drawImage( offscreen, 
                0, h, offscreen.width, lh,
                0, 0, canvas.width, canvas.height );
        }

        //------------------------
        // パレットキャンバス
        //------------------------
        if (p.cs.pal_canvas)
        {
            var pal = p.palette.color;
            if (!palette_use) {
                pal = p.pal_def.color;
            }
            if (p.screen_no == 8) {
                pal = p.pal256.color;
            }

            var canvas = p.cs.pal_canvas;
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
    //------------------------
    // 描画更新
    //------------------------
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
        case 11:
            p.update_bitmap_yae();
            break;
        case 12:
            p.update_bitmap_yjk();
            break;
        }

        // ワークスクリーン（２ページ分）にピクセルイメージを反映
        let work = p.offscreen[1];
        var ctx = work.getContext('2d');
        ctx.putImageData( p.imgData, 0, 0 );

        // ワークスクリーンからメインスクリーンにコピー
        ctx = p.offscreen[0].getContext('2d');
        if (p.interlace_mode && (5 <= p.screen_no)) {
            // 奇数行・偶数行を交互に合成
            let y = 0;
            let l0 = (p.disp_page & 254 ) * p.scan_line_count;
            let l1 = (p.disp_page       ) * p.scan_line_count;
                for (var i = 0; i < p.height;  ++i, y+=2) {
                ctx.drawImage( work, 0, i + l0, p.width, 1, 0, y    , p.width, 1 );
                ctx.drawImage( work, 0, i + l1, p.width, 1, 0, y + 1, p.width, 1 );
            }
        } else {
            // 表示ページ部分をそのまま転送
            //src領域指定が必要なら使えない → ctx.putImageData( p.imgData, 0, p.disp_page * p.height );
            let y = 0;
            if (5 <= p.screen_no) {
                y = p.disp_page * p.scan_line_count;
            }
            ctx.drawImage( work,
                 0, y, p.width, p.height,
                 0, 0, p.width, p.height );
        }

        //--------------------------------
        // スプライト
        //--------------------------------
        if (-1 < p.base.spratr) {
            //--------------------------------
            // ラスタライズ
            let mode2 = (p.screen_no < 4) ? 0 : 1;
            p.update_spr_rasterize( mode2, p.sprite16x16, p.sprite_double, 0 );

            //--------------------------------
            // ワークスクリーン（２ページ分）にピクセルイメージを反映
            let src = p.offscreen[2];
            var ctx = src.getContext('2d');
            ctx.putImageData( p.sprData, 0, 0 );
            let sd = p.sprData;//ctx.getImageData( 0, 0, src.width, p.height );

            //--------------------------------
            // メインスクリーンに合成
            if (!p.sprite_disable) {
                let dst = p.offscreen[0];
                ctx = dst.getContext('2d');
                let dd = ctx.getImageData( 0, 0, dst.width, dst.height );
                // アルファブレンド＆拡大
                let xr = src.width / dst.width;
                let yr = p.height / dst.height;
                let src_line_size = src.width * 4;
                let dst_line_size = dst.width * 4;
                for (let y = 0; y < dd.height; ++y) {
                    for (let x = 0; x < dd.width; ++x) {
                        let sx = Math.floor(x * xr);
                        let sy = Math.floor(y * yr);
                        let si = sx * 4 + sy * src_line_size;
                        if (sd.data[si + 3]) {
                            let di = x * 4 + y * dst_line_size;
                            dd.data[di + 0] = sd.data[si + 0];
                            dd.data[di + 1] = sd.data[si + 1];
                            dd.data[di + 2] = sd.data[si + 2];
                            //dd.data[di + 3] = sd.data[si + 3];
                        }
                    }
                }
                ctx.putImageData( dd, 0, 0 );
            }
        }
    }
    //------------------------
    // 表示制限ありのラスタライザ（ライン単位処理）
    // 少し重い
    update_spr_rasterize( mode2, x16, x2, tp ) 
    {
    	const p = this;

        // tp はカラーコード0を透明ではなくパレットからーで表示
        tp &= mode2; // mode 2でのみ有効

        if (!p.sprData) {
            console.log('update_chrgen - this.sprData is null.');
            return;
        }
        var pal = p.palette;
        if (!palette_use) {
            pal = p.pal_def;
        }
        if (p.screen_no == 8) {
            pal = p.pal8spr;
        }

        const pg_count = 2;
        let chr_count = 1 + x16 * 3;
        let chr_shift = x2;
        const chrw = 8 << chr_shift;
        const sprh = (8 + 8 * x16) << chr_shift;

    
        let buf = p.sprData.data;
        let d = p.vram;

        const stop_y = mode2 ? 216 : 208; // 以降非表示
        const pat_count = 256;
        const width = p.spr_scan_width;
        const height = p.spr_scan_width; 
        const dotw = 4; // rgba
        const line_size = dotw * width;

        const sprpat = p.base.sprpat;
        const sprcol = p.base.sprcol;  // mode1 : no use
        const spratr = p.base.spratr;

        let atr_y   = stop_y - 1;
        let atr_x   = 0;
        let atr_pat = 0;
        let atr_col = 0;
        const atr_size = 4;

        const EC_bit = 0x80;    // 左に32ドットずらす
        const CC_bit = 0x40;    // 若くて最も近い番号のスプライトと色をOR

        let dotcol = 15; // color
        let pgofs = 0;
        let step = 1;

        const line_limit = 4 + 4 * mode2;

        let line_buff_i = new Uint8Array(width);
        let line_buff_c = new Uint8Array(width);
        buf.fill(0);

        let spr_count = 32;
        for (var pg = 0; pg < pg_count; ++pg) {
            if (pg) spr_count = pat_count;
            let use_sprcol = mode2 && !pg;

            for (let y = 0; y < 256; ++y) {
                let line_counter = 0;
                line_buff_i.fill(0);
                line_buff_c.fill(0);
                let cur_line_cc0 = spr_count;
                for (let i = 0; i < spr_count; i+=step) {
                    if (!pg) {
                        let n = spratr + i * atr_size;
                        atr_y   = d[n + 0];
                        atr_x   = d[n + 1];
                        atr_pat = d[n + 2];
                        atr_col = d[n + 3];
                        if (atr_y == stop_y) break;
                        if (x16) atr_pat &= 0xfc;
                    } else {
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
                    let iy = (y - atr_y - 1) & 255;
                    if (sprh <= iy) continue;

                    // パターン＆カラーの参照位置補正
                    let idy = iy >> chr_shift;

                    // スプライトカラーテーブル
                    if (use_sprcol) {
                        atr_col = d[sprcol + idy + (i << 4)];
                    }
                    let cc = use_sprcol && (atr_col & CC_bit);
                    let ec_shift = (atr_col & EC_bit) >> 2;
                    
                    if (cc) {
                        if (i < cur_line_cc0) {
                            continue; // CC0が存在しない
                        }
                    } else {
                    // このラインに存在するCC=0の最新番号
                        cur_line_cc0 = i;
                    }

                    // TP=0 なら カラー0は透過
                    if (!tp && !(atr_col & 15))
                    {
                        continue;
                    }

                    // 表示
                    let pa = sprpat + atr_pat * 8 + idy;
                    let ofx = 0;
                    let shift_c = 1;
                    for (let cx = 0; cx <= x16; ++cx) {
                        let patbit = d[pa];
                        for (let ix = 0; ix < chrw; ++ix) {
                            let x = atr_x + ix + ofx;
                            x -= ec_shift;  // EC bit => 32
                            if (x < 0) continue;
                            if (255 < x) continue;
                            let dx = x * dotw + ((y & 255) + pgofs) * line_size;
                            if (patbit & 0x80) {
                                if ((!buf[ dx + 3 ])
                                 || (cc && (line_buff_i[x] == cur_line_cc0)) // CC=1のとき、直近のCC=0のピクセルならOK
                                )
                                {
                                    let col = atr_col;
                                    if (cc) {
                                        col |= line_buff_c[x]; // OR 合成
                                    } else {
                                        line_buff_i[x] = i;
                                    }
                                    col &= 15;
                                    line_buff_c[x] = col;
                                    let c = pal.rgba[ col ];
                                    buf[ dx + 0 ] = c[0];
                                    buf[ dx + 1 ] = c[1];
                                    buf[ dx + 2 ] = c[2];
                                    buf[ dx + 3 ] = 255;//c[3];
                                }
                            } else
                            if (pg) {
                                buf[ dx + 0 ] = 0;
                                buf[ dx + 1 ] = 0;
                                buf[ dx + 2 ] = 0;
                                buf[ dx + 3 ] = 255;
                            }
                            shift_c ^= chr_shift;
                            patbit <<= shift_c;
                        }
                        pa += 16; 
                        ofx += chrw;
                    }
                    //
                    line_counter += 1 - pg;
                    //if (line_counter >= line_limit) break;
                }
            }
            pgofs += 256;
            step = chr_count;
            pal = vdp.pal_def;
        }
    }
    //------------------------
    update_chrgen( chr_mask, chr_w, col_shift ) {
    	const p = this;

        if (!p.imgData) {
            console.log('update_chrgen - this.imgData is null.');
            return;
        }
        var pal = p.palette;
        if (!palette_use) {
            pal = p.pal_def;
        }
        const pg_count = p.canvas_max_page;
        let buf = p.imgData.data;
        let d = p.vram;
        let cd = p.vram;

        const patgen = p.base.patgen;
        let patcol = p.base.patcol;
        let txw = Math.floor((p.width  + chr_w - 1) / chr_w);
        let txh = (p.scan_line_count + 7) >> 3;  // / 8
        const  line_size = 4 * p.width;
        let chr_size = 4 * chr_w;

        let ndx = p.base.patnam;
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
                            if (0 <= patcol) {
                                colset = cd[patcol + (chr_d >> col_shift)];
                            }
                        }
                        let dx = dy; 
                        for(var px = 0; px < chr_w; ++px, dx+=4) {
                            let c_shift = (patbit >> 5) & 4; // 128 >> 5 = 4
                            let c = pal.rgba[ (colset >> c_shift) & 15 ];
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
            if (p.screen_no < 2) {
                txh = 8;
            }
        }
    }
    //------------------------
    update_multi_color() {
    	const p = this;

        if (!p.imgData) {
            console.log('update_multi_color - this.imgData is null.');
            return;
        }
        var pal = p.palette;
        if (!palette_use) {
            pal = p.pal_def;
        }
        const pg_count = p.canvas_max_page;
        let buf = p.imgData.data;
        let d = p.vram;

        const patnam = p.base.patnam;
        const patgen = p.base.patgen;
        const txw = (p.width  + 7) >> 3; // / 8;
        let   txh = (p.scan_line_count + 7) >> 3; // / 8;
        //const tx_size = txw * txh;
        const line_size = 4 * p.width;
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
                                var c = pal.rgba[ (colval >> c_shift) & 15 ];
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
            //txh = 32;
        }
    }
    //------------------------
    update_bitmap16() {
    	const p = this;
        if (!p.imgData) {
            console.log('update_bitmap16 - this.imgData is null.');
            return;
        }
        var pal = p.palette;
        if (!palette_use) {
            pal = p.pal_def;
        }
        const pg_count = p.canvas_max_page;
        const sz = p.width / 2 * p.scan_line_count;
        let buf = p.imgData.data;
        let d = p.vram;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let idx = p.base.patnam
                    + p.mode_info.namsiz * pg;
            for (var i = 0; i < sz; ++i) {
                let px = d[idx];
                let c = pal.rgba[px >> 4];
                buf[ odx + 0 ] = c[0];
                buf[ odx + 1 ] = c[1];
                buf[ odx + 2 ] = c[2];
                buf[ odx + 3 ] = c[3];
                c = pal.rgba[px & 15];
                buf[ odx + 4 ] = c[0];
                buf[ odx + 5 ] = c[1];
                buf[ odx + 6 ] = c[2];
                buf[ odx + 7 ] = c[3];
                odx += 8;
                idx += 1;
            }
        }
    }
    //------------------------
    update_bitmap4() {
    	const p = this;
        if (!p.imgData) {
            console.log('update_bitmap16 - this.imgData is null.');
            return;
        }
        var pal = p.palette;
        if (!palette_use) {
            pal = p.pal_def;
        }
        const pg_count = p.canvas_max_page;
        const sz = p.width / 4 * p.scan_line_count;
        let buf = p.imgData.data;
        let d = p.vram;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let idx = p.base.patnam
                    + p.mode_info.namsiz * pg;
            for (var i = 0; i < sz; ++i) {
                let px = d[idx];
                for (var c_shift = 6; c_shift>= 0; c_shift-=2 ) {
                    let c = pal.rgba[(px >> c_shift) & 3];
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
    //------------------------
    update_bitmap256() {
    	const p = this;
        if (!p.imgData) {
            console.log('update_bitmap256 - this.imgData is null.');
            return;
        }
        const pg_count = p.canvas_max_page;
        const sz = p.width * p.scan_line_count;
        let buf = p.imgData.data;
        let d = p.vram;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let idx = p.base.patnam
                    + p.mode_info.namsiz * pg;
            for (var i = 0; i < sz; ++i) {
                let px = d[idx];
                let c = p.pal256.rgba[px];
                buf[ odx + 0 ] = c[0];
                buf[ odx + 1 ] = c[1];
                buf[ odx + 2 ] = c[2];
                buf[ odx + 3 ] = c[3];
                odx += 4;
                idx += 1;
            }
        }
    }
    //------------------------
    update_bitmap_yjk() {
    	const p = this;

        if (!p.imgData) {
            console.log('update_bitmap_yjk - this.imgData is null.');
            return;
        }
        let y = [0,0,0,0];  // 0 ~ 31
        let j = 0;  // -32 ~ +31
        let k = 0;  // -32 ~ +31

        const pg_count = p.canvas_max_page;
        const sz = p.width * p.scan_line_count;
        let buf = p.imgData.data;
        let d = p.vram;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let idx = p.base.patnam
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
    //------------------------
    update_bitmap_yae() {
    	const p = this;

        if (!p.imgData) {
            console.log('update_bitmap_yae - this.imgData is null.');
            return;
        }
        let y = [0,0,0,0];  // 0 ~ 31 / bit0 == 1 -> index color
        let j = 0;  // -32 ~ +31
        let k = 0;  // -32 ~ +31

        var pal = p.palette;
        if (!palette_use) {
            pal = p.pal_def;
        }
        const pg_count = p.canvas_max_page;
        const sz = p.width * p.scan_line_count;
        let buf = p.imgData.data;
        let d = p.vram;
        let odx = 0;
        for (var pg = 0; pg < pg_count; ++pg) {
            let idx = p.base.patnam
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
                        let c = pal.rgba[ y[h] >> 1 ];
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
    //------------------------
    // 色
    //------------------------
    setColor( color )
    {
        const p = this;
        if (color === undefined) {
            color = 15;
            if (p.screen_no == 8) color = 0xff;
            if (p.screen_no == 10) color = 0xf0;
            if (p.screen_no == 11) color = 0xf0;
            if (p.screen_no == 12) color = 0xf8;
        }
        p.color = color;
    }

    //------------------------
    // 1文字出力
    //------------------------
    putChar( c, x, y, color ) {
        const p = this;
        let d = p.vram;
        const m = p.mode_info;
        const base = p.base;

        if (color === undefined) {
            color = p.color;
        }

        let txw = m.txw;
        let txh = (p.height + 7) >> 3; // height / 8;
        if (p.screen_no == 3) {
            txw = 32;
        }

        if (x < 0) return [x, y];
        if (y < 0) return [x, y];
        if (txw <= x) return [x, y];
        if (txh <= y) return [x, y];

   
        switch (p.screen_no) {
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
        const p = this;
        if (x === undefined) {
            x = p.x;
        }
        if (y === undefined) {
            y = p.y;
        }
        let sa = s.split('\n');
        for (let l = 0; l < sa.length; ++l) {
            let m = toMSX_ankChar(sa[l]);
            for (let i = 0; i < m.length; ++i) {
                let a = p.putChar( m[i], x, y, color );
                x = a[0];
                y = a[1];
            }
            x = 0;
            ++y;
        }
        p.x = x;
        p.y = y;
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
        } else {
            if (vdp.mode_info.bpp < 1) {
                // SCREEN 0～4はVRAM 0x0000～0x3FFFまるごとセーブ
            } else
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
    let disp_height = vdp.force_height ? vdp.force_height : vdp.auto_detect_height;

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
                if (!pal_not_use_vram.checked) {
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
// BMP読み込み (OpenMSXのvram2bmpで出力した物)
//  
//  openMSXでF10→コンソール
//      vram2bmp vram.bmp 0 256 2024
//      とするとVRAM全域セーブになる。
//      16bitビットマップモードではパレットも保存される。
//
// in:  d - Uint8Array
//      config - loadVcdConfig（設定オブジェクト）
// ========================================================
function get_u16(d, i) {
    return  d[i] + 
            d[i + 1] * 0x100;
}
function get_u32(d, i) {
    return  d[i] + 
            d[i + 1] * 0x100 + 
            d[i + 2] * 0x10000 + 
            d[i + 3] * 0x1000000;
}
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

    vdp.auto_detect_height = 256;
    vdp.changeScreen( vdp.screen_no, vdp.mode_info.txw, vdp.interlace_mode );
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
    if (ext_info.type == 2) {
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
            if (ext_info.ext == '.BMP') {
                let ts = loadBmp(u8array, ext_info, file_text);
                if (ts < 0) {
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
function saveAll( commpress, with_pal )
{
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
    const sel_screen_no            = document.getElementById('sel_screen_no');  // select
    const chk_screen_interlace     = document.getElementById('chk_screen_interlace'); // check
    const sel_disp_page            = document.getElementById('sel_disp_page');  // select
    const chk_sprite_use           = document.getElementById('chk_sprite_use'); // check
    const label_sprite_use         = document.getElementById('label_sprite_use');

    const detail_screen_mode_name  = document.getElementById('detail_screen_mode_name');  // span
    const detail_screen_width      = document.getElementById('detail_screen_width');  // span
    const detail_screen_height     = document.getElementById('detail_screen_height');  // span
    const detail_interlace         = document.getElementById('detail_interlace');  // span
    const detail_sprite_on         = document.getElementById('detail_sprite_on');  // span

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

    // --------------------------------------------------------
    // ファイルを開くボタン
    // --------------------------------------------------------
    const file_open_button = document.getElementById("file_open");
    const file_open_label = this.document.getElementById("file_open_label");

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
    // カラーパレットをVRAMから読み込まない
    // --------------------------------------------------------
    const pal_not_use_vram = document.getElementById('pal_not_use_vram');

    // --------------------------------------------------------
    // カラーパレットをVRAMから読み込まない
    // --------------------------------------------------------
    const pal_use_tms9918 = document.getElementById('pal_use_tms9918');

    // --------------------------------------------------------
    // カラーパレット有効/無効
    // --------------------------------------------------------
    const chk_palette_use = document.getElementById('chk_palette_use');

    // --------------------------------------------------------
    // 画面表示設定
    // --------------------------------------------------------
    const stretch_screen_radio = document.getElementsByName('stretch_screen');
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
    

    // --------------------------------------------------------
    // スプライト設定
    // --------------------------------------------------------
    const sel_sprite_mode = document.getElementById('sel_sprite_mode');
    const sel_spratr_page = document.getElementById('sel_spratr_page');
    const sel_spratr_ofs  = document.getElementById('sel_spratr_ofs');
    const sel_sprpat_page = document.getElementById('sel_sprpat_page');
    const sel_sprpat_ofs  = document.getElementById('sel_sprpat_ofs');

    // --------------------------------------------------------
    // キャンバススムージング
    // --------------------------------------------------------
    //const canvas_smoothing = document.getElementById('canvas_smoothing');

    // ========================================================
    // 処理
    // ========================================================
    // --------------------------------
    // 画面モード
    // --------------------------------
    removeAllSelectOption( sel_screen_no );
    for (let i = 0; i <= 12; ++i) {
        let o = addSelectOption(sel_screen_no, 'SCREEN ' + i, i );
        // VDPモードが被るものはスキップ
        if ((i==9) || (i==11)) {
            o.style.display = 'none'; // 表示は'block'
        }
    }
    sel_screen_no.addEventListener('change',
    function(ev) {
        let e = ev.target;
        let i = parseInt(e.options[e.selectedIndex].value);
        if (0 <= i) {
            vdp.changeScreen(i, vdp.mode_info.txw, vdp.interlace_mode );
            //vdp.cls();
            vdp.update();
            vdp.draw();
            displayCurrentFilename();
        }
    });
    // --------------------------------
    // インターレースモード
    // --------------------------------
    chk_screen_interlace.addEventListener('change',
    function(ev) {
        let e = ev.target;
        let i = e.checked ? 1 : 0;
        vdp.changeScreen(vdp.screen_no, vdp.mode_info.txw, i );
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
    // --------------------------------
    // スプライト非表示
    // --------------------------------
    if (chk_sprite_use) {
        chk_sprite_use.addEventListener('change',
        function(ev) {
            let e = ev.target;
            vdp.sprite_disable = e.checked ? 0 : 1;
            vdp.update();
            vdp.draw();
            displayCurrentFilename();
        });
    }


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
    default_log_hml = help_guide.innerHTML;
    
    // ========================================================
    // イベント：画面縦横比(DotAspect比)変更
    // ========================================================
    canvas_area.height = VDP.screen_height;
    stretch_screen_radio.forEach(e => { 
        if (e.checked) {
            vdp.aspect_ratio = Number.parseFloat(e.value);
            vdp.draw();
        }
    });
    let onChangeStrechMode = function(event) {
        const e = event.target;
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
    let onChangeHeightMode = function(event) {
        const e = event.target;
        if (e.checked) {
            vdp.force_height = Number.parseInt(e.value);

            vdp.changeScreen( vdp.screen_no, vdp.mode_info.txw, vdp.interlace_mode );
            vdp.update();
            vdp.draw();
        }
    }
    height_mode_radio.forEach(e => {
        e.addEventListener("change", onChangeHeightMode );
    });

    // ========================================================
    // イベント：TMS9918Aカラーの使用
    // ========================================================
    pal_use_tms9918.addEventListener('change', 
    function(event) {
        vdp.updateDefaultColorPalette();
        vdp.update();
        vdp.draw();
        displayCurrentFilename();
    });

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
        displayCurrentFilename();
    });
    
    // ========================================================
    // イベント：キャラクタジェネレータテーブル
    // ========================================================
    let onChangePatNam = function(e) {
        let p = sel_patnam_page;
        let o = sel_patnam_ofs;
        if (p.disabled || o.disabled) return;
        let pg = parseInt(p.options[p.selectedIndex].value);
        let of = parseInt(o.options[o.selectedIndex].value);
        vdp.setPatternNameTable( pg * vdp.mode_info.page_size + of );
        vdp.update();
        vdp.draw();
        displayCurrentScreenMode();
    }
    sel_patnam_page.addEventListener('change', onChangePatNam );
    sel_patnam_ofs .addEventListener('change', onChangePatNam );

    let onChangePatGen = function(e) {
        let p = sel_patgen_page;
        let o = sel_patgen_ofs;
        if (p.disabled || o.disabled) return;
        let pg = parseInt(p.options[p.selectedIndex].value);
        let of = parseInt(o.options[o.selectedIndex].value);
        vdp.setPatternGeneratorTable( pg * vdp.mode_info.page_size + of );
        vdp.update();
        vdp.draw();
        displayCurrentScreenMode();
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
        vdp.setPatternColorTable( pg * vdp.mode_info.page_size + of );
        vdp.update();
        vdp.draw();
        displayCurrentScreenMode();
    }
    sel_patcol_page.addEventListener('change', onChangePatCol );
    sel_patcol_ofs .addEventListener('change', onChangePatCol );

    // ========================================================
    // イベント：スプライトテーブル
    // ========================================================
    let onChangeSprAtr = function(e) {
        let p = sel_spratr_page;
        let o = sel_spratr_ofs;
        if (p.disabled || o.disabled) return;
        let pg = parseInt(p.options[p.selectedIndex].value);
        let of = parseInt(o.options[o.selectedIndex].value);
        vdp.setSpriteAttributeTable( pg * vdp.mode_info.page_size + of );
        vdp.update();
        vdp.draw();
        displayCurrentScreenMode();
    }
    sel_spratr_page.addEventListener('change', onChangeSprAtr );
    sel_spratr_ofs .addEventListener('change', onChangeSprAtr );

    let onChangeSprPat = function(e) {
        let p = sel_sprpat_page;
        let o = sel_sprpat_ofs;
        if (p.disabled || o.disabled) return;
        let pg = parseInt(p.options[p.selectedIndex].value);
        let of = parseInt(o.options[o.selectedIndex].value);
        vdp.setSpritePatternTable( pg * vdp.mode_info.page_size + of );
        vdp.update();
        vdp.draw();
        displayCurrentScreenMode();
    }
    sel_sprpat_page.addEventListener('change', onChangeSprPat );
    sel_sprpat_ofs .addEventListener('change', onChangeSprPat );

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
    // パレットファイル
    // --------------------------------------------------------
    pal_save.addEventListener("click", 
    function(e) {
        savePalette();
    });
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
    chk_palette_use.addEventListener("change", function() {
        palette_use = chk_palette_use.checked;
        vdp.update();
        vdp.draw();
        displayCurrentFilename();
    });

    ///* test
    vdp.changeScreen(5);
    vdp.sprite16x16 = 1;
    //*/

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
});

