function ret = bsusb(cmd, varargin)

%%% Example:
% bsusb('init')
% bsusb('send', '', 'SOR')
% bsusb('send', 'Trigger decs', 'CTL')
% bsusb('send', '', 'EOR')
% bsusb('close')

codes = struct('TM',   512,         ...% TM (timing) bit set
               'DV',   256,         ...% DV (data valid) bit set
               'CTL',  128,         ...% first possible stimulus
               'CTLe', 128 + 64,    ...% last+1 possible stimulus (target)
               'TRG',  32,          ...% target flag
               'SOR', 128 + 64,     ...% start of run
               'EOR', 128 + 64 + 1, ...% end of run
               'UNK', 128 + 64 + 31 ...% unknown / unspecified chunk of data
               );


switch lower(cmd)
    case 'init'
        if ~libisloaded('libbsusb')
            loadlibrary('libbsusb', 'bsusb.h');
        end
        ret = calllib('libbsusb', 'bsusb_init');
        if ret < 0
            return
        end
        snowplough = zeros(256, 1, 'uint8');
        ret = calllib('libbsusb', 'bsusb_senda', snowplough, length(snowplough));
        return
        
    case 'close'
        ret = calllib('libbsusb', 'bsusb_close');
        unloadlibrary('libbsusb');
        return
        
    case 'send'
        blk = uint8(varargin{1});
        code = 128+64+31;
        if length(varargin) > 1
            code = varargin{2};
            if ischar(code)
                code = codes.(code);
            end
        end
        
        % force a reset of the tx buffer of the UM245R
        calllib('libbsusb', 'bsusb_sendctl', 64, 0, 2, 0);
        % add code as start of message
        if ~isempty(code)
            blk = [uint8(code) blk];
        end
        % send the data
        ret = calllib('libbsusb', 'bsusb_senda', blk, length(blk));
        return
end

ret = codes.(cmd);
