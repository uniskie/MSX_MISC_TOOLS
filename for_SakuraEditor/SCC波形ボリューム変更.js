/*
	SCC�g�`�̃{�����[���ύX
	  �ԍ�  �g�`�f�[�^                         �{��(1/256)
	@s00 = {00112233445566778899aabbccddeeff
	        00112233445566778899aabbccddeeff}; 00
	
	�{�����[���Ɏw�肵�����l / 256 �̔{����������
	256�Ȃ炻�̂܂�
	128�Ȃ甼��
*/

// ���鐔
divider = 256;

// �G���[�N���X
CustomError = function(message) 
{
	this.message = message;
}
CustomError.prototype = function(message)
{
	new Error(mesasge);
}

// ���C������
try {
	// �I�����ꂽ��������擾
	//org_text = document.selection.Text; // emeditor
	org_text = Editor.GetSelectedString(0); // sakura editor
	//alert( org_text );
	
	// �󔒂�����
	str = org_text.replace(/[\s\n]/g,'')
	//alert( org_text );

	// @s nn = { nn*32 }; nn �����o��
	wave_def = str.match(/@s([0-9a-zA-Z]+)=\{([0-9a-zA-Z]{64})\};([0-9a-zA-Z]+)/i);
	if (!wave_def)
	{
		mes = 'SCC�g�`�f�[�^�̌`�����Ⴂ�܂��B\n'
			+ '@s00 = { 00*32�� }; 00 \n'
		    + str;
		throw new CustomError( mes );
	}
	//alert( '@s' + wave_def[1] + ' = {\n' + wave_def[2] + '} ; volume ' + wave_def[3] );
	inst_no_str = wave_def[1];
	wave_str    = wave_def[2];
	volume_str  = wave_def[3];

	// �y��ԍ�
	inst_no = parseInt(inst_no_str);
	//alert( 'inst_no ' + inst_no );

	// 16�i��2�� 32�ɕ���
	hexs_str = wave_str.match(/.{2}/g);
	//alert( hexs_str.join(',') );
	if (!hexs_str || (hexs_str.length != (32)))
	{
		mes = 'SCC�g�`�f�[�^��16�i��2����32�ł��B\n'
			 + str;
		if (!!hexs_str) {
			mes = mes + "\n" + hexs_str.length
		}
		throw new CustomError( mes );
	}

	// 16�i�������񂩂琔�l�ɕϊ�
	hexs = new Array();
	for (i=0; i<hexs_str.length; ++i)
	{
		v = hexs_str[i];
		hexs.push( parseInt(v, 16) ); // 16�i�������񁨐��l
	}
	//alert( hexs.join(',') );
	
	// �{�����[���i�{���j�𐔒l�ɕϊ�
	volume = parseInt(volume_str);
	//alert( 'volume = ' + volume  );
	
	// �g�`�f�[�^�ɔ{����������
	hexd = new Array();
	hexd_str = new Array();
	for (i=0; i<hexs.length; ++i)
	{
		e = hexs[i];
		if (127 < e) { e = e - 256; }
		e = Math.floor(e * volume / divider);
		if (e < 0) { e = e + 256; }
		e = Math.min(e, 255);
		e = Math.max(e, 0);
		s = ('0'+e.toString(16)).slice(-2);
		//s = s.toUpperCase();
		hexd_str.push( s );
	}
	//alert( hexs_str.join(' ') + '\n ' + volume + '/15 ->  \n' + hexd_str.join(' ') );
	
	// �����񐶐�
	new_wave = hexd_str.join('');
	out_str = '@s' + ('0'+ inst_no).slice(-2) + ' = { ' 
		+ new_wave.substring(0,32) + ' ' + new_wave.substr(32) + ' }'
	//alert( out_str );
	
	// �Ԃ�
	//document.selection.Text = ';' + org_text + '\n' + out_str + '\n'; // emeditor
	Editor.InsText( ';' + org_text + '\n' + out_str + '\n' ); // emeditor
	
}
catch (e)
{
	if (e instanceof CustomError)
	{
		alert( e.message );
	}
	else
	{
		throw e;
	}
}

// @s0={ 001931475a6a757d7f7d756a5a47311900 e7cfb9a6968b8380838b96a6b9c7e7 } ;196
// @s1={ 6060606060606060606060606060606080 90a0b0c0d0e0f00010203040506070 } ;128
// @s6={ 808ea0c0e000203f3e3c3a373129201c00 e7cfb9a6968b8380838b96a6b9c7e7 } ;64
// @s13={ 001931475a6a757d7f7d756a5a47311980 90a0b0c0d0e0f00010203040506070 } ;32
