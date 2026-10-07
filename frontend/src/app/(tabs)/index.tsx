import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { GradientBackground } from '@/components/gradient-background';
import { PreferenceToggle } from '@/components/preference-toggle';
import { PriceSliderInput } from '@/components/price-slider-input';
import { Colors } from '@/constants/colors';
import { API_BASE_URL, ENDPOINTS, USER_ID } from '@/constants/api';
import type { Preferences, SearchResponse } from '@/types';

export default function SearchScreen() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [prefsLoading, setPrefsLoading] = useState(true);

  const [cashOnly, setCashOnly] = useState(false);
  const [openPackage, setOpenPackage] = useState(false);
  const [ratingEnabled, setRatingEnabled] = useState(false);
  const [sliderValue, setSliderValue] = useState(0);

  useEffect(() => {
    loadPreferences();
  }, []);

  async function loadPreferences() {
    try {
      const res = await fetch(`${API_BASE_URL}${ENDPOINTS.preferences(USER_ID)}`);
      if (!res.ok) return;
      const prefs: Preferences = await res.json();
      setCashOnly(prefs.cash_only);
      setOpenPackage(prefs.open_package);
      setRatingEnabled(prefs.min_rating >= 4.5);
      setSliderValue(prefs.max_price ?? 0);
    } catch {
      // silently use defaults if backend unreachable on first load
    } finally {
      setPrefsLoading(false);
    }
  }

  async function handleSearch() {
    if (query.trim().length < 3) {
      Alert.alert('Căutare prea scurtă', 'Introduceți cel puțin 3 caractere.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}${ENDPOINTS.search}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, query: query.trim() }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data: SearchResponse = await res.json();
      router.push({
        pathname: '/results',
        params: {
          query: query.trim(),
          products: JSON.stringify(data.products),
          total: String(data.total),
        },
      });
    } catch {
      Alert.alert('Eroare', 'Nu am putut obține rezultate. Verificați conexiunea.');
    } finally {
      setLoading(false);
    }
  }

  if (prefsLoading) {
    return (
      <GradientBackground>
        <ActivityIndicator style={styles.centeredLoader} color={Colors.primary} size="large" />
      </GradientBackground>
    );
  }

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safe}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.flex}>
          <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
            <Text style={styles.logo}>
              <Text style={styles.logoTailor}>Tailor</Text>
              <Text style={styles.logoBuy}>Buy</Text>
            </Text>

            <View style={styles.card}>
              <View style={styles.searchRow}>
                <Text style={styles.searchIcon}>🔍</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Ce cauți astăzi?"
                  placeholderTextColor={Colors.textLight}
                  value={query}
                  onChangeText={setQuery}
                  returnKeyType="search"
                  onSubmitEditing={handleSearch}
                />
              </View>

              <Text style={styles.sectionTitle}>Preferințele tale</Text>

              <View style={styles.toggleRow}>
                <PreferenceToggle
                  label="Plată ramburs"
                  value={cashOnly}
                  onValueChange={setCashOnly}
                />
                <PreferenceToggle
                  label="Deschidere colet"
                  value={openPackage}
                  onValueChange={setOpenPackage}
                />
                <PreferenceToggle
                  label="Rating 4.5+"
                  value={ratingEnabled}
                  onValueChange={setRatingEnabled}
                />
              </View>

              <PriceSliderInput
                value={sliderValue}
                onChange={setSliderValue}
              />

              <Pressable
                style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
                onPress={handleSearch}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color={Colors.buttonText} />
                ) : (
                  <Text style={styles.buttonText}>Găsește cu AI</Text>
                )}
              </Pressable>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </GradientBackground>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  flex: { flex: 1 },
  centeredLoader: { flex: 1 },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 40,
    paddingBottom: 32,
    gap: 24,
  },
  logo: {
    fontSize: 32,
    fontWeight: '700',
    textAlign: 'center',
  },
  logoTailor: {
    color: Colors.textDark,
  },
  logoBuy: {
    color: Colors.primary,
  },
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 24,
    padding: 20,
    gap: 20,
    shadowColor: Colors.cardShadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 5,
  },
  searchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.inputBg,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    gap: 10,
  },
  searchIcon: { fontSize: 16 },
  input: {
    flex: 1,
    fontSize: 15,
    color: Colors.textDark,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textDark,
  },
  toggleRow: {
    flexDirection: 'row',
    gap: 10,
  },
  button: {
    backgroundColor: Colors.buttonBg,
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
  },
  buttonPressed: { opacity: 0.85 },
  buttonText: {
    color: Colors.buttonText,
    fontSize: 16,
    fontWeight: '700',
  },
});
