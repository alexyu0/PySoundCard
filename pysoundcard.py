from cffi import FFI
import atexit
import numpy as np
import warnings

"""PySoundCard is an audio library based on PortAudio, CFFI and NumPy

PySoundCard can play and record audio data. Audio devices are supported
through PortAudio[1], which is a free, cross-platform, open-source
audio I/O library that runs on may platforms including Windows, OS X,
and Unix (OSS/ALSA). It is accessed through CFFI[2], which is a
foreign function interface for Python calling C code. CFFI is
supported for CPython 2.6+, 3.x and PyPy 2.0+. PySoundCard represents
audio data as NumPy arrays.

PySoundCard is inspired by PyAudio[3]. Its main difference is that it
uses CFFI instead of a CPython extension and tries to implement a more
pythonic interface. Its performance characteristics are very similar.

[1]: http://www.portaudio.com/
[2]: http://cffi.readthedocs.org/
[3]: http://people.csail.mit.edu/hubert/pyaudio/

The basic building block of audio input/output in PySoundCard are
streams. Streams represent sound cards, both for audio playback and
recording. Every stream has a sample rate, a block size, an input
device and/or an output device.

There are two modes of operation for streams: read/write and callback
mode.

In read/write mode, two methods are used to play/record audio: For
playback, you write to a stream. For recording, you read from a
stream. You can read/write up to one block of audio data to a stream
without having to wait for it to play.

In callback mode, a callback function is defined, which will be called
asynchronously whenever there is a new block of audio data available
to read or write. The callback function must then provide/consume one
block of audio data.

A stream can be either full duplex (both input and output) or half
duplex (either input or output). This is determined by specifying one
or two devices for the stream. Both devices must be part of the same
audio API.

Use the function apis() to get a list of all available apis. Use the
function devices() to get a list of all available devices. There are
additional functions to get the default devices and api. If a stream
is created without specifying a device, the default devices are used.

Both devices and apis are simple dictionaries that contain information
and configuration options. Many device options can be changed simply
by modifying the dictionary before passing it to the stream
constructor. This includes the number of channels, the desired
latency, and the audio data format.

PySoundCard is BSD licensed.
(c) 2013, Bastian Bechtold

"""

ffi = FFI()
ffi.cdef("""
typedef int PaError;
typedef enum PaErrorCode
{
    paNoError = 0,

    paNotInitialized = -10000,
    paUnanticipatedHostError,
    paInvalidChannelCount,
    paInvalidSampleRate,
    paInvalidDevice,
    paInvalidFlag,
    paSampleFormatNotSupported,
    paBadIODeviceCombination,
    paInsufficientMemory,
    paBufferTooBig,
    paBufferTooSmall,
    paNullCallback,
    paBadStreamPtr,
    paTimedOut,
    paInternalError,
    paDeviceUnavailable,
    paIncompatibleHostApiSpecificStreamInfo,
    paStreamIsStopped,
    paStreamIsNotStopped,
    paInputOverflowed,
    paOutputUnderflowed,
    paHostApiNotFound,
    paInvalidHostApi,
    paCanNotReadFromACallbackStream,
    paCanNotWriteToACallbackStream,
    paCanNotReadFromAnOutputOnlyStream,
    paCanNotWriteToAnInputOnlyStream,
    paIncompatibleStreamHostApi,
    paBadBufferPtr
} PaErrorCode;

typedef enum PaHostApiTypeId
{
   paInDevelopment=0, /* use while developing support for a new host API */
   paDirectSound=1,
   paMME=2,
   paASIO=3,
   paSoundManager=4,
   paCoreAudio=5,
   paOSS=7,
   paALSA=8,
   paAL=9,
   paBeOS=10,
   paWDMKS=11,
   paJACK=12,
   paWASAPI=13,
   paAudioScienceHPI=14
} PaHostApiTypeId;

PaError Pa_Initialize(void);
PaError Pa_Terminate(void);
int Pa_GetVersion(void);
const char *Pa_GetVersionText(void);

typedef int PaDeviceIndex;

typedef struct PaHostApiInfo {
    int structVersion;
    enum PaHostApiTypeId type;
    const char *name;
    int deviceCount;
    PaDeviceIndex defaultInputDevice;
    PaDeviceIndex defaultOutputDevice;
} PaHostApiInfo;

typedef int PaHostApiIndex;

PaHostApiIndex Pa_GetHostApiCount();
const PaHostApiInfo *Pa_GetHostApiInfo(PaHostApiIndex);

typedef double PaTime;

typedef struct PaDeviceInfo {
    int structVersion;
    const char *name;
    PaHostApiIndex hostApi;
    int maxInputChannels;
    int maxOutputChannels;
    PaTime defaultLowInputLatency;
    PaTime defaultLowOutputLatency;
    PaTime defaultHighInputLatency;
    PaTime defaultHighOutputLatency;
    double defaultSampleRate;
} PaDeviceInfo;

PaDeviceIndex Pa_GetDeviceCount(void);
const PaDeviceInfo *Pa_GetDeviceInfo(PaDeviceIndex);

PaHostApiIndex Pa_GetDefaultHostApi(void);
PaDeviceIndex Pa_GetDefaultInputDevice(void);
PaDeviceIndex Pa_GetDefaultOutputDevice(void);

const char *Pa_GetErrorText(PaError);

typedef void PaStream;
typedef unsigned long PaSampleFormat;

typedef struct PaStreamParameters {
    PaDeviceIndex device;
    int channelCount;
    PaSampleFormat sampleFormat;
    PaTime suggestedLatency;
    void *hostApiSpecificStreamInfo;
} PaStreamParameters;

typedef unsigned long PaStreamFlags;

typedef struct PaStreamCallbackTimeInfo{
    PaTime inputBufferAdcTime;
    PaTime currentTime;
    PaTime outputBufferDacTime;
} PaStreamCallbackTimeInfo;

typedef unsigned long PaStreamCallbackFlags;

typedef int PaStreamCallback(const void*, void*, unsigned long,
                             const PaStreamCallbackTimeInfo*,
                             PaStreamCallbackFlags, void*);
typedef void PaStreamFinishedCallback(void*);

typedef struct PaStreamInfo {
    int structVersion;
    PaTime inputLatency;
    PaTime outputLatency;
    double sampleRate;
} PaStreamInfo;

PaError Pa_OpenStream(PaStream**, const PaStreamParameters*,
		      const PaStreamParameters*, double,
                      unsigned long, PaStreamFlags,
		      PaStreamCallback*, void*);
PaError Pa_CloseStream (PaStream*);
PaError Pa_SetStreamFinishedCallback(PaStream*, PaStreamFinishedCallback*);
PaError Pa_StartStream (PaStream*);
PaError Pa_StopStream (PaStream*);
PaError Pa_AbortStream (PaStream*);
PaError Pa_IsStreamStopped (PaStream*);
PaError Pa_IsStreamActive (PaStream*);
const PaStreamInfo *Pa_GetStreamInfo (PaStream*);
PaTime Pa_GetStreamTime (PaStream*);
double Pa_GetStreamCpuLoad (PaStream*);
PaError Pa_ReadStream (PaStream*, void*, unsigned long);
PaError Pa_WriteStream (PaStream*, const void*, unsigned long);
signed long Pa_GetStreamReadAvailable (PaStream*);
signed long Pa_GetStreamWriteAvailable (PaStream*);
PaError Pa_GetSampleSize (PaSampleFormat);
void Pa_Sleep (long);
""")


continue_flag = 0
complete_flag = 1
abort_flag = 2

_np2pa = {
    np.float32: 0x01,
    np.int32:   0x02,
    np.int16:   0x08,
    np.int8:    0x10,
    np.uint8:   0x20
}

_pa = ffi.dlopen('portaudio')
_pa.Pa_Initialize()
atexit.register(_pa.Pa_Terminate)


def _api2dict(api, index):
    if api == ffi.NULL:
        raise RuntimeError("Invalid host API info!")
    return {'struct_version': api.structVersion,
            'type': api.type,
            'name': ffi.string(api.name).decode(errors='ignore'),
            'api_idx': index,
            'device_count': api.deviceCount,
            'default_input_device_index': api.defaultInputDevice,
            'default_output_device_index': api.defaultOutputDevice}


def _dev2dict(dev, index):
    if dev == ffi.NULL:
        raise RuntimeError("Invalid device info!")
    if 'DirectSound' in list(apis())[dev.hostApi]['name']:
        enc = 'mbcs'
    else:
        enc = 'utf-8'
    return {'struct_version': dev.structVersion,
            'name': ffi.string(dev.name).decode(encoding=enc, errors='ignore'),
            'device_index': index,
            'host_api_index': dev.hostApi,
            'input_channels': dev.maxInputChannels,
            'output_channels': dev.maxOutputChannels,
            'default_low_input_latency': dev.defaultLowInputLatency,
            'default_low_output_latency': dev.defaultLowOutputLatency,
            'default_high_input_latency': dev.defaultHighInputLatency,
            'default_high_output_latency': dev.defaultHighOutputLatency,
            'default_sample_rate': dev.defaultSampleRate,
            'input_latency': dev.defaultLowInputLatency,
            'output_latency': dev.defaultLowOutputLatency,
            'sample_format': np.float32,
            'interleaved_data': True}


def apis():
    """Returns a list of all available audio apis."""
    for idx in range(_pa.Pa_GetHostApiCount()):
        yield _api2dict(_pa.Pa_GetHostApiInfo(idx), idx)


def devices():
    """Returns a list of all available audio devices."""
    for idx in range(_pa.Pa_GetDeviceCount()):
        yield _dev2dict(_pa.Pa_GetDeviceInfo(idx), idx)


def default_api():
    """Returns data about the default audio api."""
    idx = _pa.Pa_GetDefaultHostApi()
    return _api2dict(_pa.Pa_GetHostApiInfo(idx), idx)


def default_input_device():
    """Returns data about the default audio input device."""
    idx = _pa.Pa_GetDefaultInputDevice()
    return _dev2dict(_pa.Pa_GetDeviceInfo(idx), idx)


def default_output_device():
    """Returns data about the default audio output device."""
    idx = _pa.Pa_GetDefaultOutputDevice()
    return _dev2dict(_pa.Pa_GetDeviceInfo(idx), idx)


def pa_version():
    """Returns the version information about the portaudio library."""
    return (_pa.Pa_GetVersion(), ffi.string(_pa.Pa_GetVersionText()).decode())


class Stream(object):

    """Streams handle audio input and output to your application.

    Each stream operates at a specific sample rate with specific
    sample formats and buffer sizes. Each stream can either be half
    duplex (input only or output only) or full duplex (both input and
    output). For full duplex operation, the input and output device
    must use the same audio api.

    Once a stream has been created, audio processing can be started
    and stopped multiple times using start(), stop() and abort(). The
    functions is_active() and is_stopped() can be used to check this.

    The functions info(), time() and cpu_load() can be used to get
    additional information about the stream.

    Data can be read and written to the stream using read() and
    write(). Use read_length() and write_length() to see how many
    frames can be read or written at the current time.

    Alternatively, a callback can be specified which is called
    whenever there is data available to read or write.

    """

    def __init__(self, sample_rate=44100, block_length=0,
                 input_device=True, output_device=True,
                 callback=None, finished_callback=None,
                 **flags):
        """Open a new stream.

        If no sample rate is given, 44100 Hz is assumed.

        If no input or output device (or True) is specified, the
        default input/output device is taken. For input/output-only
        streams, provide None or False as input/output-device.

        The output/output device is merely a dictionary of parameters.
        Customize those parameters for more precise control over the
        device.

        If a callback is given, it will be called whenever the stream
        is active and data is available to read or write. If a
        finished_callback is given, it will be called whenever the
        stream is stopped or aborted. If a callback is given, read()
        and write() should not be used.

        The callback should have a signature like this:

        callback(input, output, time, status) -> flag

        where input is the recorded data as a NumPy array, output is
        another NumPy array (with uninitialized content), where the data
        for playback has to be written to (using indexing).
        Either input or output can be None if the stream was started
        without input or output device, respectively.
        time is a dictionary with some timing information, and
        status indicates whether input or output buffers have
        been inserted or dropped to overcome underflow or overflow
        conditions.

        The function must return one of continue_flag, complete_flag or
        abort_flag.  complete_flag and abort_flag act as if stop() or
        abort() had been called, respectively.  continue_flag resumes
        normal audio processing.

        The finished_callback should be a function with no arguments
        and no return values.

        """
        if input_device is True:
            input_device = default_input_device()
        if output_device is True:
            output_device = default_output_device()

        if input_device:
            stream_parameters_in = \
                ffi.new("PaStreamParameters*",
                        (input_device['device_index'],
                         input_device['input_channels'],
                         _np2pa[input_device['sample_format']],
                         input_device['input_latency'],
                         ffi.NULL))
            self.input_format = np.dtype(input_device['sample_format'])
            self.input_channels = stream_parameters_in.channelCount
            if stream_parameters_in and not input_device['interleaved_data']:
                stream_parameters_in.sampleFormat |= 0x80000000
        else:
            stream_parameters_in = ffi.NULL
            self.input_format = None
            self.input_channels = 0

        if output_device:
            stream_parameters_out = \
                ffi.new("PaStreamParameters*",
                        (output_device['device_index'],
                         output_device['output_channels'],
                         _np2pa[output_device['sample_format']],
                         output_device['output_latency'],
                         ffi.NULL))
            self.output_format = np.dtype(output_device['sample_format'])
            self.output_channels = stream_parameters_out.channelCount
            if stream_parameters_out and not output_device['interleaved_data']:
                stream_parameters_out.sampleFormat |= 0x80000000
        else:
            stream_parameters_out = ffi.NULL
            self.output_format = None
            self.output_channels = 0

        stream_flags = 0
        if 'no_clipping' in flags:
            stream_flags |= 0x00000001
        if 'no_dithering' in flags:
            stream_flags |= 0x00000002
        if 'never_drop_input' in flags and flags['never_drop_input']:
            stream_flags |= 0x00000004
        if 'prime_output_buffers_using_callback' in flags:
            stream_flags |= 0x00000008

        if callback:
            @ffi.callback("PaStreamCallback")
            def callback_stub(input_ptr, output_ptr, frames, time, status, _):
                if self.input_channels < 1:
                    input = None
                else:
                    num_bytes = (self.input_channels *
                                 self.input_format.itemsize * frames)
                    input = np.frombuffer(ffi.buffer(input_ptr, num_bytes),
                                          dtype=self.input_format)
                    input.shape = -1, self.input_channels

                if self.output_channels < 1:
                    output = None
                else:
                    num_bytes = (self.output_channels *
                                 self.output_format.itemsize * frames)
                    output = np.frombuffer(ffi.buffer(output_ptr, num_bytes),
                                           dtype=self.output_format)
                    output.shape = -1, self.output_channels

                time = {'input_adc_time': time.inputBufferAdcTime,
                        'current_time': time.currentTime,
                        'output_dac_time': time.outputBufferDacTime}
                return callback(input, output, time, status)

            self._callback = callback_stub
        else:
            self._callback = ffi.NULL

        self._stream = ffi.new("PaStream**")
        err = _pa.Pa_OpenStream(self._stream, stream_parameters_in or ffi.NULL,
                                stream_parameters_out or ffi.NULL, sample_rate,
                                block_length, stream_flags, self._callback,
                                ffi.NULL)
        self._handle_error(err)

        # dereference PaStream** --> PaStream*
        self._stream = self._stream[0]

        # set some stream information
        self.sample_rate = sample_rate
        self.block_length = block_length
        info = _pa.Pa_GetStreamInfo(self._stream)
        if info == ffi.NULL:
            raise RuntimeError("Could not obtain stream info!")
        self.input_latency = info.inputLatency,
        self.output_latency = info.outputLatency,

        if finished_callback:
            @ffi.callback("PaStreamFinishedCallback")
            def finished_callback_stub(userData):
                finished_callback()
            self._finished_callback = finished_callback_stub
            err = _pa.Pa_SetStreamFinishedCallback(self._stream,
                                                   self._finished_callback)
            self._handle_error(err)

    # Avoid confusion if something goes wrong before assigning self._stream:
    _stream = ffi.NULL

    def _handle_error(self, err):
        # all error codes are negative:
        if err >= 0:
            return err
        errstr = ffi.string(_pa.Pa_GetErrorText(err)).decode()
        if err == -9981 or err == -9980:
            # InputOverflowed and OuputUnderflowed are non-fatal:
            warnings.warn("%.4f: %s" % (self.time(), errstr),
                          RuntimeWarning, stacklevel=2)
            return err
        else:
            raise RuntimeError("%.4f: %s" % (self.time(), errstr))

    def __del__(self):
        # Close stream at garbage collection
        self.close()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, tb):
        self.stop()
        self.close()

    def start(self):
        """Commence audio processing.

        If successful, the stream is considered active.

        """
        err = _pa.Pa_StartStream(self._stream)
        if err == _pa.paStreamIsNotStopped:
            return
        self._handle_error(err)

    def stop(self):
        """Terminate audio processing.

        This waits until all pending audio buffers have been played
        before it returns. If successful, the stream is considered
        inactive.

        """
        err = _pa.Pa_StopStream(self._stream)
        if err == _pa.paStreamIsStopped:
            return
        self._handle_error(err)

    def abort(self):
        """Terminate audio processing immediately.

        This does not wait for pending audio buffers. If successful,
        the stream is considered inactive.

        """
        err = _pa.Pa_AbortStream(self._stream)
        if err == _pa.paStreamIsStopped:
            return
        self._handle_error(err)

    def close(self):
        """Close the stream.

        Can be called multiple times.
        If the audio stream is active any pending buffers are discarded
        as if abort() had been called.

        """
        _pa.Pa_CloseStream(self._stream)
        # There might be errors if _pa.Pa_Terminate() has been called
        # already or if the stream has been closed before.
        # Those errors are ignored here, it's too late anyway ...

    def is_active(self):
        """Determine whether the stream is active.

        A stream is active after a successful call to start(). It
        becomes inactive as a result to stop() or abort() or a return
        value other than continue from the stream callback.

        """
        return self._handle_error(_pa.Pa_IsStreamActive(self._stream)) == 1

    def is_stopped(self):
        """Determine whether a stream is stopped.

        A stream is stopped before the first call to start() and after
        a successful call to stop() or abort(). If the stream callback
        returns a value other than continue, the stream is NOT
        considered stopped.

        """
        return self._handle_error(_pa.Pa_IsStreamStopped(self._stream)) == 1

    def read_length(self):
        """The number of frames that can be written without waiting."""
        return _pa.Pa_GetStreamReadAvailable(self._stream)

    def write_length(self):
        """The number of frames that can be read without waiting."""
        return _pa.Pa_GetStreamWriteAvailable(self._stream)

    def time(self):
        """Returns the current stream time in seconds.

        This is the same time that is given to the stream callback. It
        is monotonically increasing and is not affected by starting or
        stopping the stream. This time may be used for synchronizing
        other events to the audio stream.

        """
        return _pa.Pa_GetStreamTime(self._stream)

    def cpu_load(self):
        """Retrieve CPU usage information for the specified stream.

        A floating point number between 0.0 and 1.0 that is a fraction
        of the total CPU time consumed by the stream callback audio
        processing within portaudio. This excludes time spent in the
        cffi and Python. This function does not work with blocking
        read/write streams.

        """
        return _pa.Pa_GetStreamCpuLoad(self._stream)

    def read(self, num_frames, raw=False):
        """Read samples from an input stream.

        The function does not return until the required number of
        frames has been read. This may involve waiting for the
        operating system to supply the data.

        If raw data is requested, the raw cffi data buffer is
        returned. Otherwise, a numpy array of the appropriate dtype
        with one column per channel is returned.

        """
        num_bytes = (self.input_channels * self.input_format.itemsize *
                     num_frames)
        data = ffi.new("signed char[]", num_bytes)
        self._handle_error(_pa.Pa_ReadStream(self._stream, data, frames))
        if not raw:
            data = np.frombuffer(ffi.buffer(data), dtype=self.input_format)
            data.shape = frames, self.input_channels
        return data

    def write(self, data):
        """Write samples to an output stream.

        As much as one block_length of audio data will be played
        without blocking. If more than one block_length was provided,
        the function will only return when all but one block_length
        has been played.

        Data will be converted to a numpy matrix. Multichannel data
        should be provided as a (num_frames, channels) matrix. If the
        data is provided as a 1-dim array, it will be treated as mono
        data and will be played on all channels simultaneously. If the
        data is provided as a 2-dim matrix and fewer tracks are
        provided than channels, silence will be played on the missing
        channels. Similarly, if more tracks are provided than there
        are channels, the extraneous channels will not be played.

        """
        num_frames = len(data)
        num_channels = self.output_channels

        if (not isinstance(data, np.ndarray) or
                data.dtype != self.output_format):
            data = np.array(data, dtype=self.output_format)
        if len(data.shape) == 1:
            # broadcast 1D arrays to (n,1) matrices
            data = np.asmatrix(data).T
        elif len(data.shape) == 2 and data.shape[1] == 1:
            # play mono signals on all channels
            data = np.tile(data, (1, num_channels))
        if data.shape[1] > num_channels:
            data = data[:, :num_channels]
        if data.shape < (num_frames, num_channels):
            # if less data is available than requested, pad with zeros.
            tmp = data
            data = np.zeros((num_frames, num_channels),
                            dtype=self.output_format)
            data[:tmp.shape[0], :tmp.shape[1]] = tmp

        data = data.ravel().tostring()
        err = _pa.Pa_WriteStream(self._stream, data, num_frames)
        self._handle_error(err)


if __name__ == '__main__':
    from scipy.io.wavfile import read as wavread
    import time
    fs, wave = wavread('thistle.wav')
    wave = np.array(wave, dtype=np.float32)
    wave /= 2**15
    block_length = 4

    def callback(in_data, frame_count, time_info, status):
        if status != 0:
            print(status)
        return (in_data, continue_flag)
    s = Stream(sample_rate=fs, block_length=block_length, callback=callback)
    s.start()
    # for n in range(int(fs*5/block_length)):
    #     s.write(s.read(block_length))
    # for idx in range(0, wave.size, block_length):
    #     s.write(wave[idx:idx+block_length])
    time.sleep(5)
    s.stop()
