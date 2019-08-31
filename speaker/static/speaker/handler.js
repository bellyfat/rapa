var OpusEncoderProcessor = function (wsh) {
    this.wsh = wsh;
    //this.bufferSize = 4096; // for webaudio script processor
    //this.downSample = 2;
    //this.opusFrameDur = 60; // msec
    //this.opusRate = 24000;
    this.bufferSize = 4096; // for webaudio script processor
    this.downSample = 1;
    this.opusFrameDur = 40; // msec
    this.opusRate = 48000;
    this.channelNumber = 2;
    this.i16arr = new Int16Array((this.bufferSize / this.downSample) * this.channelNumber);
    this.f32arr = new Float32Array((this.bufferSize / this.downSample) * this.channelNumber);
    this.opusEncoder = new OpusEncoder(this.opusRate, this.channelNumber, 2049, this.opusFrameDur);
}

OpusEncoderProcessor.prototype.onAudioProcess = function (e) {
    if (isRecording) {
        var data = e.inputBuffer.getChannelData(0);
        var data_channel_2 = e.inputBuffer.getChannelData(1);
        var i = 0;
        var ds = this.downSample;

        if (encode) {
            i = 0;
            for (var idx = 0; idx < data.length; idx += ds) {
                this.f32arr[i * 2] = data[idx];
                this.f32arr[i * 2 + 1] = data_channel_2[idx];
                i++;
            }

            var res = this.opusEncoder.encode_float(this.f32arr);

            for (var idx = 0; idx < res.length; ++idx) {
                this.wsh.send(res[idx]);
            }
        } else {
            for (var idx = 0; idx < data.length; idx += ds) {
                this.i16arr[i++] = data[idx] * 0xFFFF; // int16
            }

            this.wsh.send(this.i16arr);
        }
    }
}

var MediaHandler = function (audioProcessor) {
    var context = new(window.AudioContext || window.webkitAudioContext)();
    if (!context.createScriptProcessor) {
        context.createScriptProcessor = context.createJavaScriptNode;
    }

    if (context.sampleRate < 44000 || context.SampleRate > 50000) {
        alert("Unsupported sample rate: " + String(context.sampleRate));
        return;
    };

    //initialize mic
    navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia;

    this.context = context;
    this.audioProcessor = audioProcessor;
    var userMediaConfig = {
        "audio": {
            "mandatory": {},
            "optional": []
        }
    }

    navigator.getUserMedia(userMediaConfig, this.callback.bind(this), this.error);
    //navigator.mediaDevices.getUserMedia(userMediaConfig)
    //.then(this.callback.bind(this))
    //.catch(this.error);
}

MediaHandler.prototype.callback = function (stream) {
    console.log('starting callback');
    this.micSource = this.context.createMediaStreamSource(stream);
    this.processor = this.context.createScriptProcessor(this.audioProcessor.bufferSize, 2);
    this.processor.onaudioprocess = this.audioProcessor.onAudioProcess.bind(this.audioProcessor);
    this.micSource.connect(this.processor);
    this.processor.connect(this.context.destination);
    console.log('ending callback');
}

MediaHandler.prototype.error = function (err) {
    alert("Problem");
}