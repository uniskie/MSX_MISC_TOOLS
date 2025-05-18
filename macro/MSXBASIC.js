/**
 *	「MSX BASIC LIST を アスキーリスト化してエディタに書き出す」
 *	- 文字化け回避のために元ファイルを直接読み込む
 *	- 文字化け回避のために"元のファイル名.ASC"で変換後のテキストを直接保存
 *
 *	  ** 同じファイル名のファイルがあっても
 *		 問い合わせ無しに上書きするので、注意してください。 **
 *
 *	テキストエディタ MACRO (サクラエディタ/EmEditor)
 *	もしくは WSH（cscript）で動作
 */

//==========================================================
// MSX BASIC トークンデータ
//==========================================================

// 数値トークン
var oct_token		= 0x0B;	// 8進数
var hex_token		= 0x0C;	// 16進数
var line_adr_token	= 0x0D;	// アドレス化済み行番号（※セーブリストには存在しない）
var line_num_token	= 0x0E;	// 行番号
var int8b_token		= 0x0F;	// 整数（10～255）
var int0_token		= 0x11; // 整数（0～9）
var int9_token		= 0x1A;	//    〃
var int16b_token	= 0x1C;	// 整数（256～32767）
var single_token	= 0x1D;	// 単精度実数
var double_token	= 0x1F;	// 倍精度実数

// 文字列囲い
var quote_token = 0x22;	// " （ダブルクオーテーション）
// DATA REM 以後、行末まで文字列
var data_token  = 0x84;	// DATA

// 特殊組み合わせ
// $3A $8F $E6  ... '    ( `:REM $E6` を `'` に置換)
// $3A $A1      ... ELSE ( `:ELSE` を `ELSE` に置換)
// $FF XX       ... ff_tokens
var colon_token = 0x3A;	// :
var rem_token   = 0x8F;	// REM
var rem_token_2 = 0xE6;	// '
var else_token  = 0xA1;	// ELSE


// コマンドトークン
var cmd_token_s = 0x81;
var cmd_token_e = 0xFC;
var cmd_token_list = [
// $81 - $FC
	"END",		"FOR",		"NEXT",		"DATA",		
	"INPUT",	"DIM",		"READ",		"LET",		
	"GOTO",		"RUN",		"IF",		"RESTORE",	
	"GOSUB",	"RETURN",	"REM",		"STOP",		
	"PRINT",	"CLEAR",	"LIST",		"NEW",		
	"ON",		"WAIT",		"DEF",		"POKE",		
	"CONT",		"CSAVE",	"CLOAD",	"OUT",		
	"LPRINT",	"LLIST",	"CLS",		"WIDTH",	
	"ELSE",		"TRON",		"TROFF",	"SWAP",		
	"ERASE",	"ERROR",	"RESUME",	"DELETE",	
	"AUTO",		"RENUM",	"DEFSTR",	"DEFINT",	
	"DEFSNG",	"DEFDBL",	"LINE",		"OPEN",		
	"FIELD",	"GET",		"PUT",		"CLOSE",	
	"LOAD",		"MERGE",	"FILES",	"LSET",		
	"RSET",		"SAVE",		"LFILES",	"CIRCLE",	
	"COLOR",	"DRAW",		"PAINT",	"BEEP",		
	"PLAY",		"PSET",		"PRESET",	"SOUND",	
	"SCREEN",	"VPOKE",	"SPRITE",	"VDP",		
	"BASE",		"CALL",		"TIME",		"KEY",		
	"MAX",		"MOTOR",	"BLOAD",	"BSAVE",	
	"DSKO$",	"SET",		"NAME",		"KILL",		
	"IPL",		"COPY",		"CMD",		"LOCATE",	
	"TO",		"THEN",		"TAB(",		"STEP",		
	"USR",		"FN",		"SPC(",		"NOT",		
	"ERL",		"ERR",		"STRING$",	"USING",	
	"INSTR",	"[']",		"VARPTR",	"CSRLIN",	
	"ATTR$",	"DSKI$",	"OFF",		"INKEY$",	
	"POINT",	">",		"=",		"<",		
	"+",		"-",		"*",		"/",		
	"^",		"AND",		"OR",		"XOR",		
	"EQV",		"INP",		"MOD",		"\\",		
];

// コマンドトークン （FF XX）
var ff_token   = 0xFF;
var ff_token_s = 0x81;
var ff_token_e = 0xB0;
var ff_token_list = [
	// $ff $81 - $ff $B0
	"LEFT$",	"RIGHT$",	"MID$",		"SGN",		
	"INT",		"ABS",		"SQR",		"RND",		
	"SIN",		"LOG",		"EXP",		"COS",		
	"TAN",		"ATN",		"FRE",		"INP",		
	"POS",		"LEN",		"STR$",		"VAL",		
	"ASC",		"CHR$",		"PEEK",		"VPEEK",	
	"SPACE$",	"OCT$",		"HEX$",		"LPOS",		
	"BIN$",		"CNT",		"CSNG",		"CDBL",		
	"FIX",		"STICK",	"STRIG",	"PDL",		
	"PAD",		"DSKF",		"FPOS",		"CVI",		
	"CVS",		"CVD",		"EOF",		"LOC",		
	"LOF",		"MKI$",		"MKS$",		"MKD$"		
];

//==========================================================
// Editor依存関数系
//==========================================================
var shell = new ActiveXObject( "WScript.Shell" );
function efunc(){}

efunc.isEditor = false;
efunc.emEditor = false;
efunc.sakuraEditor = false;

try{
	// emEditor
	(editor.Version > 0); // is EmEditor ? 

	efunc.emEditor = true;
	efunc.isEditor = true;

//	efunc.inputBox = function( msg, def )	{	return prompt( msg, def );	}
	efunc.alertBox = function( s, o )		{	if(o==null) { alert( s ); }else{ alert( s, o ); }	}
	efunc.isSelectionEmpty = function()		{	return document.selection.IsEmpty;	}
//	efunc.selectLine = function()			{	document.selection.SelectLine();	}
	efunc.getSelectionText = function()		{	return document.selection.Text;	}
	efunc.selectAll = function()			{	document.selection.SelectAll();	}
	efunc.setText = function( s )			{	document.selection.Text = s;	}
	efunc.getFullName = function()			{	return document.FullName;	}
	efunc.getPosX = function()				{	return document.selection.GetActivePointX( eePosView );	}
	efunc.getPosY = function()				{	return document.selection.GetActivePointY( eePosView );	}
	efunc.setPos = function( x, y )			{	document.selection.SetActivePoint( eePosView, x, y ); }
}catch(e){
	efunc.emEditor = false;
	efunc.isEditor = false;
}
if (!efunc.emEditor) {
try{
	Editor.IsPossibleUndo;	// is SakuraEditor?

	efunc.sakuraEditor = true;
	efunc.isEditor = true;

//	efunc.inputBox = function( msg, def )	{	return Editor.InputBox( msg, def, 8 );	}
	efunc.alertBox = function( s, o )		{	if(o==null) { Editor.InfoMsg( s ); }else{ Editor.InfoMsg( s + "\n" + o ); }	}
	efunc.isSelectionEmpty = function()		{	return (Editor.IsTextSelected == 0);	}
//	efunc.selectLine = function()			{	Editor.SelectLine();	}
	efunc.getSelectionText = function()		{	return Editor.GetSelectedString();	}
	efunc.selectAll = function()			{	Editor.SelectAll( 0 );	}
	efunc.setText = function( s )			{	Editor.InsText( s );	}
	efunc.getFullName = function()			{	return Editor.GetFilename();	}
	efunc.getPosX = function()				{	return Editor.GetSelectColumnFrom();	}
	efunc.getPosY = function()				{	return Editor.GetSelectLineFrom();	}
	efunc.setPos = function( x, y )			{	Editor.MoveCursor( y, x, 0 );	}
}catch(e){
	efunc.sakuraEditor = false;
	efunc.isEditor = false;
}
}
if (!efunc.isEditor) {
	// テキストエディタではない = WScript

	//	efunc.inputBox = function( msg, def )	{shell.Popup( '入力できないのでデフォルト値を使います', 0, msg ); return def;	}
	//	efunc.alertBox = function( s, o )		{return shell.Popup( s, 0, o );}
	efunc.alertBox = function( s, o )		{if(o==null){WScript.Echo( s );} else {WScript.Echo( s + "\n" + o );}}
	efunc.isSelectionEmpty = function()		{return true;	}
	//	efunc.selectLine = function()			{}
	efunc.getSelectionText = function()		{return "";	}
	efunc.selectAll = function()			{}
	efunc.setText = function( s )			{}
	efunc.getFullName = function()			{return "";	}
	efunc.getPosX = function()				{return 0;	}
	efunc.getPosY = function()				{return 0;	}
	efunc.setPos = function( x, y )			{}
}
//==========================================================


//==========================================================
// ADODB.Stream 定数
//==========================================================
// StreamTypeEnum
var adTypeBinary = 1; // バイナリ
var adTypeText   = 2; // テキスト
// StreamReadEnum
var adReadAll  = -1; // 全行
var adReadLine = -2; // 一行ごと
// StreamWriteEnum
var adWriteChar = 0; // 改行なし
var adWriteLine = 1; // 改行あり
// SaveOptionsEnum 
var adSaveCreateNotExist  = 1; // ない場合は新規作成
var adSaveCreateOverWrite = 2; // ある場合は上書き

//==========================================================
// ADODB.Stream での バイナリ・エンコード 処理系
//==========================================================
function bin2hex(binStr){
	var xmldom = new ActiveXObject("Microsoft.XMLDOM");
	var binObj= xmldom.createElement("binObj");
	binObj.dataType = 'bin.hex';
	binObj.nodeTypedValue = binStr;
	return(String(binObj.text));
}

function hex2bin(hexStr){
	var xmldom = new ActiveXObject("Microsoft.XMLDOM");
	var binObj= xmldom.createElement("binObj");
	binObj.dataType = 'bin.hex';
	binObj.text = hexStr;
	return(binObj.nodeTypedValue);
}

function str2hex( ascStr ){
	var hex = new Array;
	for(var i = 0; i < ascStr.length; ++i) {
		var h = "0" + ascStr.charCodeAt(i).toString(16);
		hex.push( h.substring(h.length-2) );
	}
	return hex.join('');
}

function hex2array( hexStr ){
	var ar = new Array;
	for(var i = 0; i < hexStr.length; i+=2 ) {
		ar.push( parseInt("0x"+hexStr.substring(i,i+2)) );
	}
	return ar;
}

//function array2hex( ar ){
//	var hex = new Array;
//	for(var i = 0; i < ar.length; i++ ) {
//		var h = "0" + ar[i].toString(16);
//		hex.push( h.substring(h.length-2) );
//	}
//	return hex.join('');
//}

//function uniucode2sjis_bin( text ) {
//	var ado = new ActiveXObject("ADODB.Stream");
//	ado.Open();
//	ado.Type = adTypeText;
//	ado.Charset = "Shift_JIS";
//	text = ado.WriteText( text, adWriteChar );
//
//	ado.Position = 0;
//	ado.Type = adTypeBinary;
//	var bin = ado.Read();
//	ado.CLose();
//	ado = null;
//	return bin;
//}

function sjis2unicode( text ) {
	var hexStr = str2hex( text );
	var xmldom = new ActiveXObject("Microsoft.XMLDOM");
	var binObj= xmldom.createElement("binObj");
	binObj.dataType = 'bin.hex';
	binObj.text =  hexStr;
	//efunc.alertBox("hex ", hexStr);

	var ado = new ActiveXObject("ADODB.Stream");
	ado.Open();

	ado.Type = adTypeBinary;
	ado.Write( binObj.nodeTypedValue );

	ado.Position = 0;
	ado.Type = adTypeText;
	ado.Charset = "Shift_JIS";
	text = ado.ReadText( adReadAll );
	
	//efunc.alertBox("unicode",text);
	
	ado.CLose();
	ado = null;
	
	return text;
}

function loadBinaryFile( path ) {
	//efunc.alertBox("path", path);
	var ado = new ActiveXObject("ADODB.Stream");
	ado.Open();
	ado.Type = adTypeBinary;
	ado.LoadFromFile( path );
	var bin = ado.Read();
	ado.CLose();
	ado = null;
	return bin;
}

function saveBinaryFile( path, bin ) {
	//efunc.alertBox("path", path);
	var ado = new ActiveXObject("ADODB.Stream");
	ado.Open();
	ado.Type = adTypeBinary;
	ado.Write( bin );
	ado.SaveToFile( path, adSaveCreateOverWrite );
	ado.CLose();
	ado = null;
	return bin;
}

//function saveTextFile( text, path ) {
//	//efunc.alertBox("path", path);
//	var ado = new ActiveXObject("ADODB.Stream");
//	ado.Open();
//	ado.Type = adTypeText;
//	ado.Charset = "Shift_JIS";
//	ado.WriteText( text, adWriteChar );
//	ado.SaveToFile( path, adSaveCreateOverWrite );
//	ado.CLose();
//	ado = null;
//}

//function hex2num( src, pos )
//{
//	pos += pos;
//	if (src.length <= (pos+1)) return 0;
//	return parseInt("0x" + src.substring(pos, pos+2));
//}

//==========================================================
// 浮動小数点数のMSX BASIC表現
// (single! ) EE XX XX XX (仮数部はDAC)
// (double# ) EE XX XX XX XX XX XX XX (仮数部はDAC)
//==========================================================
function toPrecisionStr( hex, deco ) {

	var siglen = hex.length - 2;
	var e = parseInt("0x" + hex.substring(0,2));
	e = (e & 0x7f) - 64;

	var t = "0." + hex.substring(2, siglen+2).replace(/0+$/, '');
	var es = Math.abs(e).toString(10);
	if (e < 0) { t = t + "E-" + es; }
	else       { t = t + "E+" + es; }

	var v = parseFloat(t);

	t = v.toExponential(siglen);
	e = parseInt(t.replace(/[^e]+e/i,''));	// E以降の指数
	var sig = t.replace(/0*e.+/i,'');	// Eより手前の数値を0サプレス
	var fraclen = sig.length - 2;		//（0サプレスしたあとの）小数点以下の桁数

	if ((-3 < e) && (e < fraclen)) {
		t = v.toString(10).replace(/0\./, '.');
	}
	else if ((fraclen <= e) && (e < siglen)  ){
		t = v.toString(10) + deco;
	}
	else {
		es = "0" + Math.abs(e).toString(10);
		es = es.substring( es.length - 2 );
		if (e < 0) { t = sig + "E-" + es; }
		else       { t = sig + "E+" + es; }
	}
	return t;
}

//==========================================================
// MSX BASIC トークンの解読・ASCII形式リスト作成
//==========================================================
function decodeBasic( input_path, output_filenmae )
{
	// emeditorは0x00が0x20に化けるので
	// NG→ var bin = uniucode2sjis_bin( src_text );
	// OK↓ 元ファイルから直接読み込む
	var bin = loadBinaryFile( input_path );

	// jsではWSH.Binary型を扱えないので、
	// Binary型→HEX文字列→整数Array
	var hex = bin2hex( bin );
	//saveTextFile( hex, path + "\\" + "hex_temp.txt" )
	var dat = hex2array( hex );
	// 浮動小数点数の処理で手抜きをするために残す → hex = null;

	var dat_len = dat.length;
	var p = 0;
	var lines = new Array;
	var pointers = new Array;
	
	if (dat[p++] != 0xff) {
		//efunc.alertBox("test");
		efunc.alertBox(input_path + "は 中間言語形式 ではありません", "header 0x"  + dat[0].toString(16) + " != 0xFF");
		return "";
	}
	
	while (p < dat_len) {
		if ((p+2) > dat_len) {
			// エラー抜け
			efunc.alertBox("リストが中断されました", "in " + lines.length);
			break;
		}

		var link_ptr = dat[p++] + dat[p++] * 256;
		if (link_ptr == 0) {
			break;	// 終端
		}

		if ((p+2) > dat_len) {
			// エラー抜け
			efunc.alertBox("リストが中断されました", lines.length);
			break;
		}
		var line_no =  dat[p++] + dat[p++] * 256;

		var text = line_no.toString(10) + " ";
		var dquote = false;
		var quoted = false;

		while (p < dat_len) {
			var c = dat[p];
			var c2 = dat[p+1];
			var c3 = dat[p+2];
			p++;

			if (c == 0) {
				// line end
				break;
			}

			var t = String.fromCharCode(c);

			if (c == quote_token) {
			// double quotation
				dquote = !dquote;
			}

			if (dquote || quoted) {
				// 文字列
			}
			else
			if (c == colon_token) {
				// 3A 8F E6 = "'"
				if ((c2 == rem_token) && (c3 ==  rem_token_2)) {
					t = "";
				}
				// 3A A1 = "ELSE"
				if (c2 == else_token) {
					t = "";
				}
			}
			else
			// token
			if ((cmd_token_s <= c) && (c <= cmd_token_e)) {
				if ((c == rem_token) && (c2 == rem_token_2)) {
				// 3A 8F E6 = ":REM" E6 = "'"
					t = "'";
					p++;
					quoted = true;	// 以下、文字列扱い
				}
				else
				{
					t = cmd_token_list[c - cmd_token_s];
				}
				if (c == rem_token || c == data_token) {
					quoted = true;	// 以下、文字列扱い
				}
			}
			else
			// FF token
			if (c == ff_token) {
				if ((ff_token_s <= c2) && (c2 <= ff_token_e)) {
					p++;
					t = ff_token_list[c2 - ff_token_s];
				}
			}
			else
			// (oct) &O XX XX
			if (c == oct_token) {
				t = "&O" + (c2 + c3 * 256).toString(8);
				p += 2;
			}
			else
			// (hex) &H XX XX
			if (c == hex_token) {
				t = "&H" + (c2 + c3 * 256).toString(16).toUpperCase();
				p += 2;
			}
			else
			// (line address) XX XX
			if (c == line_adr_token) {
				var adr = (c2 + c3 * 256) - 0x8000;
				var ln = dat[adr] + dat[adr + 1] * 256;
				t = ln.toString(10);
				p += 2;
			}
			else
			// (line number) XX XX
			if (c == line_num_token) {
				t = (c2 + c3 * 256).toString(10);
				p += 2;
			}
			else
			// (int% 10 ~ 255) XX
			if (c == int8b_token) {
				t = c2.toString(10)
				p += 1;
			}
			else
			// (int% 0 ~ 9)
			if ((int0_token <= c) && (c <= int9_token)) {
				t = (c - 0x11).toString(10)
			}
			else
			// (int% 256 ~ 32767) XX XX
			if (c == int16b_token) {
				t = (c2 + c3 * 256).toString(10);
				p += 2;
			}
			else
			// (single! ) EE XX XX XX (仮数部はDAC)
			if (c == single_token) {
				t = toPrecisionStr( hex.substring((p+0)*2, (p+4)*2), '!');
				p += 4;
			}
			else
			// (double# ) EE XX XX XX XX XX XX XX (仮数部はDAC)
			if (c == double_token) {
				t = toPrecisionStr( hex.substring((p+0)*2, (p+8)*2), '#');
				p += 8;
			}
			text += t;

		}
		pointers.push( link_ptr );
		lines.push( text );
	}

	var ascStr = lines.join("\r\n") + "\r\n" + String.fromCharCode(0x1A);
	
	if (output_filenmae.length) {
		saveBinaryFile( output_filenmae, hex2bin( str2hex(ascStr) ) );
	}
	
	return sjis2unicode( ascStr );
}

//==========================================================
// メイン処理
//==========================================================
if (efunc.isEditor) {
	var x = efunc.getPosX();
	var y = efunc.getPosY();
	var input_path = efunc.getFullName();
	var output_path = input_path + ".ASC"
	var ret = decodeBasic( input_path, output_path );
	if (ret.length) {
		efunc.selectAll()
		efunc.setText( ret );
		efunc.setPos( x, y );
	}
} else {
	var input_path = WScript.Arguments(0).toUpperCase()
	var output_path = input_path + ".ASC"
	var ret = decodeBasic( input_path, output_path );
	if (ret.length) {
		WScript.Echo( ret );
		WScript.Echo( 'MSXBASICアスキーリスト変換: "'+ output_path + '"を保存しました。' );
	}
}

