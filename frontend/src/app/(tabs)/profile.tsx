import Slider from '@react-native-community/slider';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
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
import { ENDPOINTS } from '@/constants/api';
import { useAuth } from '@/context/AuthContext';
import { apiRequest } from '@/services/api';
import type { Preferences } from '@/types';

export default function ProfileScreen() {
  const { user, refreshUser, logout } = useAuth();

  // ── Account edit state ────────────────────────────────────────────────
  const [editingAccount, setEditingAccount] = useState(false);
  const [editEmail, setEditEmail] = useState('');
  const [editNickname, setEditNickname] = useState('');
  const [savingAccount, setSavingAccount] = useState(false);

  // ── Change password state ─────────────────────────────────────────────
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);

  // ── Preferences state ─────────────────────────────────────────────────
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [cashOnly, setCashOnly] = useState(false);
  const [openPackage, setOpenPackage] = useState(false);
  const [ratingEnabled, setRatingEnabled] = useState(false);
  const [newOnly, setNewOnly] = useState(false);
  const [sliderValue, setSliderValue] = useState(0);
  const [minReviewCount, setMinReviewCount] = useState(0);
  const [searchEmag, setSearchEmag] = useState(true);
  const [searchAltex, setSearchAltex] = useState(true);

  useEffect(() => {
    loadPreferences();
  }, []);

  async function loadPreferences() {
    try {
      const res = await apiRequest(ENDPOINTS.preferences);
      if (!res.ok) throw new Error();
      const prefs: Preferences = await res.json();
      setCashOnly(prefs.cash_only);
      setOpenPackage(prefs.open_package);
      setRatingEnabled(prefs.min_rating >= 4.5);
      setNewOnly(prefs.new_only);
      setSliderValue(prefs.max_price ?? 0);
      setMinReviewCount(prefs.min_review_count ?? 0);
      setSearchEmag(prefs.search_emag);
      setSearchAltex(prefs.search_altex);
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

  async function handleSavePreferences() {
    setSaving(true);
    try {
      const res = await apiRequest(ENDPOINTS.preferences, {
        method: 'PUT',
        body: JSON.stringify({
          cash_only: cashOnly,
          open_package: openPackage,
          min_rating: ratingEnabled ? 4.5 : 0.0,
          max_price: sliderValue === 0 ? null : sliderValue,
          min_review_count: minReviewCount === 0 ? null : minReviewCount,
          new_only: newOnly,
          search_emag: searchEmag,
          search_altex: searchAltex,
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

  function startEditAccount() {
    setEditEmail(user?.email ?? '');
    setEditNickname(user?.nickname ?? '');
    setEditingAccount(true);
  }

  async function handleSaveAccount() {
    setSavingAccount(true);
    try {
      const res = await apiRequest(ENDPOINTS.authMe, {
        method: 'PUT',
        body: JSON.stringify({
          email: editEmail.trim() || null,
          nickname: editNickname.trim() || null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(typeof err?.detail === 'string' ? err.detail : 'Eroare');
      }
      await refreshUser();
      setEditingAccount(false);
      Alert.alert('Salvat', 'Datele contului au fost actualizate.');
    } catch (err: any) {
      Alert.alert('Eroare', err?.message ?? 'Nu am putut salva datele.');
    } finally {
      setSavingAccount(false);
    }
  }

  async function handleChangePassword() {
    if (!currentPassword || !newPassword || !confirmPassword) {
      Alert.alert('Câmpuri lipsă', 'Completează toate câmpurile pentru schimbarea parolei.');
      return;
    }
    if (newPassword !== confirmPassword) {
      Alert.alert('Parolă nepotrivită', 'Parola nouă și confirmarea nu coincid.');
      return;
    }
    if (newPassword.length < 8) {
      Alert.alert('Parolă prea scurtă', 'Parola nouă trebuie să aibă cel puțin 8 caractere.');
      return;
    }

    setSavingPassword(true);
    try {
      const res = await apiRequest(ENDPOINTS.authChangePassword, {
        method: 'POST',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(typeof err?.detail === 'string' ? err.detail : 'Eroare');
      }
      Alert.alert(
        'Parolă schimbată',
        'Parola a fost schimbată. Vei fi deconectat pe toate dispozitivele.',
        [{ text: 'OK', onPress: () => logout() }]
      );
    } catch (err: any) {
      Alert.alert('Eroare', err?.message ?? 'Nu am putut schimba parola.');
    } finally {
      setSavingPassword(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
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

          {/* ── Account card ───────────────────────────────────────────── */}
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Contul meu</Text>

            {editingAccount ? (
              <>
                <View style={styles.inputRow}>
                  <TextInput
                    style={styles.input}
                    value={editNickname}
                    onChangeText={setEditNickname}
                    placeholder="Nickname"
                    placeholderTextColor={Colors.textLight}
                    autoCapitalize="words"
                  />
                </View>
                <View style={styles.inputRow}>
                  <TextInput
                    style={styles.input}
                    value={editEmail}
                    onChangeText={setEditEmail}
                    placeholder="Email"
                    placeholderTextColor={Colors.textLight}
                    keyboardType="email-address"
                    autoCapitalize="none"
                  />
                </View>
                <View style={styles.buttonRow}>
                  <Pressable
                    style={[styles.button, styles.buttonOutline, styles.flex]}
                    onPress={() => setEditingAccount(false)}
                  >
                    <Text style={styles.buttonOutlineText}>Anulează</Text>
                  </Pressable>
                  <Pressable
                    style={[styles.button, styles.flex]}
                    onPress={handleSaveAccount}
                    disabled={savingAccount}
                  >
                    {savingAccount ? (
                      <ActivityIndicator color={Colors.buttonText} />
                    ) : (
                      <Text style={styles.buttonText}>Salvează</Text>
                    )}
                  </Pressable>
                </View>
              </>
            ) : (
              <>
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Nickname</Text>
                  <Text style={styles.infoValue}>{user?.nickname ?? '—'}</Text>
                </View>
                <View style={styles.infoRow}>
                  <Text style={styles.infoLabel}>Email</Text>
                  <Text style={styles.infoValue}>{user?.email}</Text>
                </View>
                <Pressable
                  style={({ pressed }) => [styles.button, styles.buttonOutline, pressed && styles.buttonPressed]}
                  onPress={startEditAccount}
                >
                  <Text style={styles.buttonOutlineText}>Modifică datele</Text>
                </Pressable>
              </>
            )}
          </View>

          {/* ── Change password card ────────────────────────────────────── */}
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Schimbă parola</Text>

            <View style={styles.inputRow}>
              <TextInput
                style={styles.input}
                value={currentPassword}
                onChangeText={setCurrentPassword}
                placeholder="Parola curentă"
                placeholderTextColor={Colors.textLight}
                secureTextEntry
              />
            </View>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.input}
                value={newPassword}
                onChangeText={setNewPassword}
                placeholder="Parola nouă (min. 8 caractere)"
                placeholderTextColor={Colors.textLight}
                secureTextEntry
              />
            </View>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.input}
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                placeholder="Confirmă parola nouă"
                placeholderTextColor={Colors.textLight}
                secureTextEntry
                returnKeyType="done"
                onSubmitEditing={handleChangePassword}
              />
            </View>

            <Pressable
              style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
              onPress={handleChangePassword}
              disabled={savingPassword}
            >
              {savingPassword ? (
                <ActivityIndicator color={Colors.buttonText} />
              ) : (
                <Text style={styles.buttonText}>Schimbă parola</Text>
              )}
            </Pressable>
          </View>

          {/* ── Preferences card ────────────────────────────────────────── */}
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Preferințe de cumpărare</Text>

            <View style={styles.toggleRow}>
              <PreferenceToggle label="Plată ramburs" value={cashOnly} onValueChange={markDirty(setCashOnly)} />
              <PreferenceToggle label="Deschidere colet" value={openPackage} onValueChange={markDirty(setOpenPackage)} />
              <PreferenceToggle label="Rating 4.5+" value={ratingEnabled} onValueChange={markDirty(setRatingEnabled)} />
            </View>

            <View style={styles.toggleRow}>
              <PreferenceToggle label="Doar produse noi" value={newOnly} onValueChange={markDirty(setNewOnly)} />
            </View>

            <PriceSliderInput
              value={sliderValue}
              onChange={(v) => { setSliderValue(v); setDirty(true); }}
            />

            <View style={styles.sliderSection}>
              <View style={styles.sliderHeader}>
                <Text style={styles.sliderLabel}>Recenzii minime</Text>
                <Text style={styles.sliderValue}>
                  {minReviewCount === 0 ? 'Fără restricție' : `Minim ${minReviewCount}`}
                </Text>
              </View>
              <Slider
                value={minReviewCount}
                onValueChange={(v) => { setMinReviewCount(Math.round(v / 5) * 5); setDirty(true); }}
                minimumValue={0}
                maximumValue={200}
                step={5}
                minimumTrackTintColor={Colors.primary}
                maximumTrackTintColor={Colors.toggleInactive}
                thumbTintColor={Colors.primary}
              />
            </View>

            <View style={styles.storeSection}>
              <Text style={styles.sectionTitle}>Magazine</Text>
              <View style={styles.toggleRow}>
                <PreferenceToggle label="eMAG" value={searchEmag} onValueChange={markDirty(setSearchEmag)} />
                <PreferenceToggle label="Altex" value={searchAltex} onValueChange={markDirty(setSearchAltex)} />
              </View>
            </View>

            <Pressable
              style={({ pressed }) => [
                styles.button,
                !dirty && styles.buttonDisabled,
                pressed && dirty && styles.buttonPressed,
              ]}
              onPress={handleSavePreferences}
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

          {/* ── Logout ──────────────────────────────────────────────────── */}
          <Pressable
            style={({ pressed }) => [styles.logoutButton, pressed && styles.buttonPressed]}
            onPress={() =>
              Alert.alert('Deconectare', 'Ești sigur că vrei să te deconectezi?', [
                { text: 'Anulează', style: 'cancel' },
                { text: 'Deconectează', style: 'destructive', onPress: logout },
              ])
            }
          >
            <Text style={styles.logoutText}>Deconectare</Text>
          </Pressable>

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
    gap: 16,
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
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  infoLabel: {
    fontSize: 14,
    color: Colors.textMid,
    fontWeight: '500',
  },
  infoValue: {
    fontSize: 14,
    color: Colors.textDark,
    fontWeight: '600',
  },
  inputRow: {
    backgroundColor: Colors.inputBg,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  input: {
    fontSize: 15,
    color: Colors.textDark,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
  },
  flex: { flex: 1 },
  button: {
    backgroundColor: Colors.buttonBg,
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: 'center',
  },
  buttonOutline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: Colors.primary,
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
  buttonOutlineText: {
    color: Colors.primary,
    fontSize: 15,
    fontWeight: '700',
  },
  toggleRow: {
    flexDirection: 'row',
    gap: 10,
  },
  sliderSection: { gap: 4 },
  sliderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sliderLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textDark,
  },
  sliderValue: {
    fontSize: 13,
    color: Colors.primary,
    fontWeight: '600',
  },
  storeSection: { gap: 12 },
  logoutButton: {
    borderRadius: 16,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#ef4444',
  },
  logoutText: {
    color: '#ef4444',
    fontSize: 15,
    fontWeight: '700',
  },
});
