import os
import subprocess
import requests
from flask import Flask, request, jsonify
import asyncio
import edge_tts

app = Flask(__name__)

# नई आवाज़ (Audio) बनाने के लिए फ्री Edge-TTS का इस्तेमाल
async def generate_voice(text, output_audio_path, lang_code="hi-IN"):
    # हिंदी के लिए hi-IN-MadhuramNeural या अंग्रेजी के लिए en-US-AriaNeural
    voice = "hi-IN-MadhuramNeural" if "hi" in lang_code else "en-US-AriaNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio_path)

@app.route('/dub', methods=['POST'])
def dub_video():
    data = request.json
    video_url = data.get('video_url')
    translated_text = data.get('text')
    lang_code = data.get('lang', 'hi')

    # फ़ाइल नाम सेट करना
    input_video = "input.mp4"
    translated_audio = "translated.mp3"
    output_video = "final_dubbed.mp4"

    try:
        # 1. वीडियो डाउनलोड करें
        response = requests.get(video_url)
        with open(input_video, 'wb') as f:
            f.write(response.content)

        # 2. ट्रांसलेटेड टेक्स्ट से नया ऑडियो जनरेट करें
        asyncio.run(generate_voice(translated_text, translated_audio, lang_code))

        # 3. FFmpeg के ज़रिए पुराना ऑडियो हटाकर नया ऑडियो मर्ज करें
        ffmpeg_cmd = [
            'ffmpeg', '-y', 
            '-i', input_video,         # इनपुट वीडियो
            '-i', translated_audio,     # नया डब किया हुआ ऑडियो
            '-c:v', 'copy',             # वीडियो को बिना री-एन्कोड किए कॉपी करें (तेज़ होगा)
            '-map', '0:v:0',            # पहला इनपुट वीडियो ट्रैक लें
            '-map', '1:a:0',            # दूसरा इनपुट ऑडियो ट्रैक लें
            '-shortest',                # जो छोटा हो वहां वीडियो खत्म करें
            output_video
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # यहाँ आप चाहें तो फाइनल वीडियो को Google Drive या किसी फ्री स्टोरेज पर अपलोड कर सकते हैं
        return jsonify({
            "status": "success", 
            "message": "Video dubbed successfully!", 
            "download_url": "सर्वर_पर_वीडियो_का_पाथ"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
  
