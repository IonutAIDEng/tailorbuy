import Slider from '@react-native-community/slider';
import { useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { Colors } from '@/constants/colors';

const MAX_PRICE_LIMIT = 10000;

interface Props {
  value: number;
  onChange: (v: number) => void;
}

export function PriceSliderInput({ value, onChange }: Props) {
  const [isEditing, setIsEditing] = useState(false);
  const [inputText, setInputText] = useState('');
  const [error, setError] = useState('');
  const lastTapRef = useRef(0);

  function handleTap() {
    const now = Date.now();
    if (now - lastTapRef.current < 350) {
      setInputText(value === 0 ? '' : String(value));
      setError('');
      setIsEditing(true);
    }
    lastTapRef.current = now;
  }

  function commit() {
    const trimmed = inputText.trim();
    if (trimmed === '' || trimmed === '0') {
      onChange(0);
      setIsEditing(false);
      setError('');
      return;
    }
    const num = parseInt(trimmed, 10);
    if (num > MAX_PRICE_LIMIT) {
      setError(`Maximum ${MAX_PRICE_LIMIT} RON`);
      return;
    }
    onChange(num);
    setIsEditing(false);
    setError('');
  }

  function handleBlur() {
    const trimmed = inputText.trim();
    if (trimmed === '' || trimmed === '0') {
      onChange(0);
    } else {
      const num = parseInt(trimmed, 10);
      if (!isNaN(num) && num >= 1 && num <= MAX_PRICE_LIMIT) {
        onChange(num);
      }
    }
    setIsEditing(false);
    setError('');
  }

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Preț maxim</Text>

      <View style={styles.rangeRow}>
        <Text style={styles.rangeMin}>0</Text>
        {isEditing ? (
          <View style={styles.inputRow}>
            <TextInput
              style={[styles.input, error ? styles.inputError : null]}
              value={inputText}
              onChangeText={(t) => {
                setInputText(t.replace(/[^0-9]/g, ''));
                setError('');
              }}
              onSubmitEditing={commit}
              onBlur={handleBlur}
              keyboardType="numeric"
              returnKeyType="done"
              maxLength={5}
              placeholder="0"
              placeholderTextColor={Colors.textLight}
              autoFocus
            />
            <Text style={[styles.suffix, error ? styles.suffixError : null]}>RON</Text>
          </View>
        ) : (
          <Pressable onPress={handleTap} hitSlop={8} testID="price-value-tap">
            <Text style={styles.currentValue}>
              {value === 0 ? 'Orice preț' : `${value} RON`}
            </Text>
          </Pressable>
        )}
      </View>

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <Slider
        style={styles.slider}
        minimumValue={0}
        maximumValue={MAX_PRICE_LIMIT}
        step={50}
        value={value}
        onValueChange={(v) => onChange(Math.round(v))}
        minimumTrackTintColor={Colors.primary}
        maximumTrackTintColor={Colors.toggleInactive}
        thumbTintColor={Colors.primary}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 6 },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textDark,
  },
  rangeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rangeMin: {
    fontSize: 11,
    color: Colors.textMid,
  },
  currentValue: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.primary,
    textDecorationLine: 'underline',
    textDecorationStyle: 'dotted',
    textDecorationColor: Colors.primary,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  input: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.primary,
    borderBottomWidth: 2,
    borderBottomColor: Colors.primary,
    minWidth: 52,
    textAlign: 'right',
    paddingVertical: 2,
    paddingHorizontal: 4,
  },
  inputError: {
    borderBottomColor: Colors.errorRed,
    color: Colors.errorRed,
  },
  suffix: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.primary,
  },
  suffixError: {
    color: Colors.errorRed,
  },
  errorText: {
    fontSize: 12,
    color: Colors.errorRed,
    fontWeight: '500',
    textAlign: 'right',
  },
  slider: { width: '100%', height: 40 },
});
