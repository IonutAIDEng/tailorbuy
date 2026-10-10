import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
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
import { Colors } from '@/constants/colors';
import { API_BASE_URL, ENDPOINTS, USER_ID } from '@/constants/api';
import type { Preferences, SearchResponse } from '@/types';

export default function SearchScreen() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [prefsLoading, setPrefsLoading] = useState(true);
  const [prefs, setPrefs] = useState<Preferences | null>(null);

  useFocusEffect(
    useCallback(() => {
      loadPreferences();
    }, [])
  );

  async function loadPreferences() {
    try {
      const res = await fetch(`${API_BASE_URL}${ENDPOINTS.preferences(USER_ID)}`);
      if (!res.ok) return;
      const data: Preferences = await res.json();
      setPrefs(data);
    } catch {
      // silently use no-filter display if backend unreachable
    } finally {
      setPrefsLoading(false);
    }
  }

  function buildActiveChips(p: Preferences): string[] {
    const chips: string[] = [];
    if (p.cash_only) chips.push('💳 Ramburs');
    if (p.open_package) chips.push('📦 Deschidere colet');
    if (p.min_rating >= 4.5) chips.push('⭐ Rating 4.5+');
    if (p.max_price) chips.push(`💰 Max ${p.max_price} RON`);
    if (p.new_only) chips.push('✨ Produse noi');
    if (p.min_review_count) chips.push(`💬 Min ${p.min_review_count} recenzii`);
    const stores: string[] = [];
    if (p.search_emag) stores.push('eMAG');
    if (p.search_altex) stores.push('Altex');
    chips.push(`🏪 ${stores.length > 0 ? stores.join(' & ') : 'eMAG & Altex'}`);
    return chips;
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
        const errorData = await res.json().catch(() => ({}));
        if (res.status === 429) {
          const detail = errorData?.detail;
          const message = detail?.message ?? 'Prea multe cereri. Revino mai târziu.';
          Alert.alert('Limită atinsă', message);
          return;
        }
        throw new Error(`HTTP ${res.status}`);
      }

      const data: SearchResponse = await res.json();
      router.push({
        pathname: '/results',
        params: {
          query: query.trim(),
          products: JSON.stringify(data.products),
          total: String(data.total),
          message: data.message ?? '',
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

  const activeChips = prefs ? buildActiveChips(prefs) : [];

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

              <View style={styles.filtersHeader}>
                <Text style={styles.sectionTitle}>Filtre active</Text>
                <Pressable onPress={() => router.push('/(tabs)/profile')}>
                  <Text style={styles.editLink}>Modifică →</Text>
                </Pressable>
              </View>

              {activeChips.length === 0 ? (
                <Text style={styles.noFilters}>Fără filtre active</Text>
              ) : (
                <View style={styles.chipsRow}>
                  {activeChips.map((chip) => (
                    <View key={chip} style={styles.chip}>
                      <Text style={styles.chipText}>{chip}</Text>
                    </View>
                  ))}
                </View>
              )}

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
  logoTailor: { color: Colors.textDark },
  logoBuy: { color: Colors.primary },
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 24,
    padding: 20,
    gap: 16,
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
  filtersHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.textDark,
  },
  editLink: {
    fontSize: 13,
    color: Colors.primary,
    fontWeight: '600',
  },
  noFilters: {
    fontSize: 13,
    color: Colors.textMid,
    fontStyle: 'italic',
  },
  chipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    backgroundColor: Colors.inputBg,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chipText: {
    fontSize: 12,
    color: Colors.textDark,
    fontWeight: '500',
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
