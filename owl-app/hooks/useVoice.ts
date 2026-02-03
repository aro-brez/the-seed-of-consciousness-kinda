import { useState, useCallback, useRef } from 'react';
import * as Speech from 'expo-speech';
import { config } from '@/constants/config';

export function useVoice() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const currentSpeechId = useRef<string | null>(null);

  const speak = useCallback(async (text: string) => {
    // Stop any current speech
    if (isSpeaking) {
      await Speech.stop();
    }

    const speechId = Date.now().toString();
    currentSpeechId.current = speechId;
    setIsSpeaking(true);

    return new Promise<void>((resolve) => {
      Speech.speak(text, {
        rate: config.speechRate,
        pitch: config.speechPitch,
        onDone: () => {
          if (currentSpeechId.current === speechId) {
            setIsSpeaking(false);
          }
          resolve();
        },
        onError: () => {
          if (currentSpeechId.current === speechId) {
            setIsSpeaking(false);
          }
          resolve();
        },
        onStopped: () => {
          if (currentSpeechId.current === speechId) {
            setIsSpeaking(false);
          }
          resolve();
        },
      });
    });
  }, [isSpeaking]);

  const stopSpeaking = useCallback(async () => {
    currentSpeechId.current = null;
    await Speech.stop();
    setIsSpeaking(false);
  }, []);

  // Note: Full voice recognition requires expo-av recording + external API
  // This is a placeholder for the listening UI state
  const startListening = useCallback(() => {
    setIsListening(true);
  }, []);

  const stopListening = useCallback(() => {
    setIsListening(false);
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  return {
    isSpeaking,
    isListening,
    speak,
    stopSpeaking,
    startListening,
    stopListening,
    toggleListening,
  };
}
