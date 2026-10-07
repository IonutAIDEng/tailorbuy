import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { GradientBackground } from '@/components/gradient-background';
import { PreferenceToggle } from '@/components/preference-toggle';
import { PriceSliderInput } from '@/components/price-slider-input';
import { Colors } from '@/constants/colors';
import { API_BASE_URL, ENDPOINTS, USER_ID } from '@/constants/api';
import type { Preferences } from '@/types';

export default function ProfileScreen() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

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
      if (!res.ok) throw new Error();
      const prefs: Preferences = await res.json();
      setCashOnly(prefs.cash_only);
      setOpenPackage(prefs.open_package);
      setRatingEnabled(prefs.min_rating >= 4.5);
      setSliderValue(prefs.max_price ?? 0);
    } catch {
      Alert.alert('Eroare', 'Nu am putut încărca preferințele.');
    } finally {
      setLoading(false);
    }
  }

  function markDirty<T>(setter: (v: T) => void) {
    return (v: T) => {
      setter(v);
      setDirty(true);
    };
  }

  async function handleSave() {
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE_URL}${ENDPOINTS.preferences(USER_ID)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cash_only: cashOnly,
          open_package: openPackage,
          min_rating: ratingEnabled ? 4.5 : 0.0,
          max_price: sliderValue === 0 ? null : sliderValue,
        }),
      });

      if (!res.ok) throw new Error();
      setDirty(false);
      Alert.alert('Salvat', 'Preferințele au fost actualizate.');
    } catch {
      Alert.alert('Eroare', 'Nu am putut salva preferințele.');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <GradientBackground>
        <ActivityIndicator style={styles.centeredLoader} color={Colors.primary} size="large" />
      </GradientBackground>
    );
  }

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safe}>
        <ScrollView contentContainerStyle={styles.scroll}>
          <Text style={styles.title}>Profilul meu</Text>

          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Preferințe de cumpărare</Text>

            <View style={styles.toggleRow}>
              <PreferenceToggle
                label="Plată ramburs"
                value={cashOnly}
                onValueChange={markDirty(setCashOnly)}
              />
              <PreferenceToggle
                label="Deschidere colet"
                value={openPackage}
                onValueChange={markDirty(setOpenPackage)}
              />
              <PreferenceToggle
                label="Rating 4.5+"
                value={ratingEnabled}
                onValueChange={markDirty(setRatingEnabled)}
              />
            </View>

            <PriceSliderInput
              value={sliderValue}
              onChange={(v) => {
                setSliderValue(v);
                setDirty(true);
              }}
            />

            <Pressable
              style={({ pressed }) => [
                styles.button,
                !dirty && styles.buttonDisabled,
                pressed && dirty && styles.buttonPressed,
              ]}
              onPress={handleSave}
              disabled={!dirty || saving}
            >
              {saving ? (
                <ActivityIndicator color={Colors.buttonText} />
              ) : (
                <Text style={styles.buttonText}>
                  {dirty ? 'Salvează preferințele' : 'Preferințe salvate'}
                </Text>
              )}
            </Pressable>
          </View>

          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>Cont</Text>
            <Text style={styles.infoRow}>
              <Text style={styles.infoLabel}>ID utilizator: </Text>
              <Text style={styles.infoValue}>{USER_ID}</Text>
            </Text>
            <Text style={styles.infoNote}>
              Autentificarea completă va fi disponibilă într-o versiune viitoare.
            </Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    </GradientBackground>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  centeredLoader: { flex: 1 },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 40,
    paddingBottom: 32,
    gap: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.textDark,
    textAlign: 'center',
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
  buttonDisabled: {
    backgroundColor: Colors.toggleInactive,
  },
  buttonPressed: { opacity: 0.85 },
  buttonText: {
    color: Colors.buttonText,
    fontSize: 15,
    fontWeight: '700',
  },
  infoCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 24,
    padding: 20,
    gap: 8,
    shadowColor: Colors.cardShadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  infoTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.textDark,
    marginBottom: 4,
  },
  infoRow: { fontSize: 14 },
  infoLabel: { color: Colors.textMid, fontWeight: '500' },
  infoValue: { color: Colors.textDark, fontWeight: '600' },
  infoNote: {
    fontSize: 12,
    color: Colors.textMid,
    fontStyle: 'italic',
    marginTop: 4,
  },
});
