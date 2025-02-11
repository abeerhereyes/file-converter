import React, { useState } from 'react';
import axios from 'axios';
import './converter.css';

function Converter() {
    const [file, setFile] = useState(null);
    const [format, setFormat] = useState('');
    const [response, setResponse] = useState('');
    const [fileType, setFileType] = useState(null); // 'audio', 'video', 'text', 'pdf'
    const [isFileUploaded, setIsFileUploaded] = useState(false);

    const videoFormats = [
        'mp4', 'm4v', 'mp4v',
        '3gp', '3g2', 'avi',
        'mov', 'wmv', 'mkv',
        'flv', 'ogv', 'webm',
        'h264', '264', 'hevc',
        '265'
    ];

    const audioFormats = [
        'mp3', 'wav', 'ogg',
        'aac', 'wma', 'flac',
        'm4a'
    ];

    const textFormats = [
        'txt', 'doc', 'docx',
        'pdf', 'odt', 'rtf'
    ];

    const onFileChange = (e) => {
        const uploadedFile = e.target.files[0];
        setFile(uploadedFile);
        setIsFileUploaded(true);

        // Determine file type based on MIME type or extension
        const fileExtension = uploadedFile.name.split('.').pop().toLowerCase();
        if (uploadedFile.type.startsWith('audio/') || audioFormats.includes(fileExtension)) {
            setFileType('audio');
            setFormat('mp3'); // Default audio format
        } else if (uploadedFile.type.startsWith('video/') || videoFormats.includes(fileExtension)) {
            setFileType('video');
            setFormat('mp4'); // Default video format
        } else if (uploadedFile.type === 'text/plain' || textFormats.includes(fileExtension)) {
            setFileType('text');
            setFormat('pdf'); // Default text format
        } else if (fileExtension === 'pdf') {
            setFileType('pdf');
            setFormat('txt'); // Default PDF format
        } else {
            setFileType(null);
            setResponse('Unsupported file type.');
        }
    };

    const onFormatChange = (e) => {
        setFormat(e.target.value);
    };

    const onSubmit = async (e) => {
        e.preventDefault();
        if (!file || !format) {
            setResponse('Please upload a file and select a format.');
            return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("format", format);

        try {
            const res = await axios.post('https://file-converter-64qn.onrender.com', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `converted.${format}`);
            document.body.appendChild(link);
            link.click();
            setResponse('File converted and downloaded successfully!');
        } catch (err) {
            if (err.response && err.response.data) {
                const reader = new FileReader();
                reader.onload = () => {
                    const errorMessage = JSON.parse(reader.result).error;
                    setResponse(`Error: ${errorMessage}`);
                };
                reader.readAsText(err.response.data);
            } else {
                setResponse('An unexpected error occurred.');
            }
        }
    };

    return (
        <>
       <div className='intro-content'>
        <div className='content'>

        <h1 className='h1-text'>Free File Converter</h1>
        <p className='basic-p'>
            Your go-to online tool for <span className='impo-p'>FREE</span> and <span className='impo-p'>UNLIMITED</span> file conversion with audio, video, and text files.
        </p>
        </div>
        </div>
        <div className="upload-container">
            <h2>File Converter</h2>
            <form onSubmit={onSubmit} className="upload-form">
                <input 
                    type="file" 
                    onChange={onFileChange} 
                    className="file-input"
                    accept="*/*" 
                    />

                {isFileUploaded && fileType && (
                    <div className="format-selectors">
                        <label htmlFor="format" className="format-label">
                            Convert to:
                            <select 
                                value={format} 
                                onChange={onFormatChange} 
                                className="format-select"
                                id="format"
                                >
                                {fileType===""}
                                {fileType === "audio" && (audioFormats.map(fmt =>(
                                    <option key={fmt} value={fmt}>
                                        {fmt.toUpperCase()}
                                    </option>
                                )))}
                                {(fileType === 'video') && (
                                    <>
                                        <optgroup label="Video Formats">
                                            {videoFormats.map(fmt => (
                                                <option key={fmt} value={fmt}>
                                                    {fmt.toUpperCase()}
                                                </option>
                                            ))}
                                        </optgroup>
                                        <optgroup label="Audio Formats">
                                            {audioFormats.map(fmt => (
                                                <option key={fmt} value={fmt}>
                                                    {fmt.toUpperCase()}
                                                </option>
                                            ))}
                                        </optgroup>
                                    </>
                                )}
                              
                                {(fileType === 'text' || fileType === 'pdf') && (
                                    textFormats.map(fmt => (
                                        <option key={fmt} value={fmt}>
                                            {fmt.toUpperCase()}
                                        </option>
                                    ))
                                )}
                            </select>
                        </label>
                    </div>
                )}

                {isFileUploaded && (
                    <button type="submit" className="btn upload-btn">
                        Convert
                    </button>
                )}
            </form>

            {response && <p className="response-message">{response}</p>}
        </div>
        </>
    );
}

export default Converter;