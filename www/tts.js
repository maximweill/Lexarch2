
function speakWord(text) {
    if ('speechSynthesis' in window) {
        var msg = new SpeechSynthesisUtterance();
        msg.text = text; msg.lang = 'en-US'; msg.rate = 0.85; 
        window.speechSynthesis.cancel(); window.speechSynthesis.speak(msg);
    }
}
