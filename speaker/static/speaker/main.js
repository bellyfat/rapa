
var isRecording = false;
var encode = true;
var audio_stream = null;
var audio_processor = null;
var media_handler = null;

var audio_record = null;

$(function() {
//var wsh = new WebSocket( 'ws://' + window.location.href.split( '/' )[2] + '/ws' );

//function onWsMessage( msg ){ console.log(msg); }

//wsh.onmessage = onWsMessage;
//var ap = new OpusEncoderProcessor( wsh );
//var mh = new MediaHandler( ap );
getDeviceList();
});

function getDeviceList() {
    device_list = $("#device-list")[0];
    $.getJSON("get_device_list", (data, status) => {
        for (i = device_list.options.length - 1; i >= 0; i--) {
            device_list.remove(i);
        }
        for (var index in data) {
            if (data.hasOwnProperty(index)) {
                var new_option = $("<option>")[0];
                new_option.value = data[index].name;
                new_option.innerText = data[index].name;
                device_list.append(new_option);
            }
        }
    })
}

function sendSettings()
{
    if( document.getElementById( "encode" ).checked )
    {
        encode = 1;
    } else {
        encode = 0;
    }

    var rate = String( mh.context.sampleRate / ap.downSample );
    var opusRate = String( ap.opusRate );
    var opusFrameDur = String( ap.opusFrameDur )

    var msg = "m:" + [ rate, encode, opusRate, opusFrameDur ].join( "," );
    console.log( msg );
    wsh.send( msg );
}

function startRecord()
{
    document.getElementById( "record").innerHTML = "Stop";
    document.getElementById( "encode" ).disabled = true;
    audio_processor = new OpusEncoderProcessor( audio_stream );
    media_handler = new MediaHandler( audio_processor );
    media_handler.context.resume(); // needs an await?
    //sendSettings();
    isRecording = true;
    console.log( 'started recording' );
}

function stopRecord()
{
    isRecording  = false;
    document.getElementById( "record").innerHTML = "Record";
    document.getElementById( "encode" ).disabled = false;
    media_handler.context.close();
    console.log( 'ended recording' );
}

function toggleRecord()
{
    if( isRecording ) {
        audio_stream.close();
        audio_stream = null;
    } else {
        //audio_stream = new WebSocket( 'ws://' + window.location.href.split( '/' )[2] + '/ws' );
        audio_stream = new WebSocket( 'ws://192.168.0.104:8000/ws/speaker/audioplayback/' );
        audio_stream.onopen = startRecord;
        audio_stream.onclose = stopRecord;
    }
}

function recordLocal() {
    audio_stream = new WebSocket( 'ws://192.168.0.104:8000/ws/speaker/audioplayback/' );
    audio_record = new WebSocket( 'ws://localhost:8000/ws/speaker/audiorecord/' );
    audio_record.onmessage = function (message) {
        audio_stream.send(message.data);
    }
}

function stopLocalRecord() {
    audio_stream.close();
    audio_record.close();
}
