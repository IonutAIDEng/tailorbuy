import { router } from 'expo-router';
import { useState } from 'react';
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
import { useAuth } from '@/context/AuthContext';

export default function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    if (!email.trim() || !password) {
      Alert.alert('Câmpuri lipsă', 'Completează email-ul și parola.');
      return;
    }
    setLoading(true);
    try {
      await login(email.trim(), password);
    } catch (err: any) {
      Alert.alert('Eroare', err?.message ?? 'Autentificare eșuată.');
    } finally {
      setLoading(false);
    }
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
            <Text style={styles.subtitle}>Conectează-te la contul tău</Text>

            <View style={styles.card}>
              <View style={styles.inputRow}>
                <TextInput
                  style={styles.input}
                  value={email}
                  onChangeText={setEmail}
                  placeholder="Email"
                  placeholderTextColor={Colors.textLight}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  returnKeyType="next"
                />
              </View>

              <View style={styles.inputRow}>
                <TextInput
                  style={styles.input}
                  value={password}
                  onChangeText={setPassword}
                  placeholder="Parolă"
                  placeholderTextColor={Colors.textLight}
                  secureTextEntry
                  returnKeyType="done"
                  onSubmitEditing={handleLogin}
                />
              </View>

              <Pressable
                style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
                onPress={handleLogin}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color={Colors.buttonText} />
                ) : (
                  <Text style={styles.buttonText}>Conectează-te</Text>
                )}
              </Pressable>

              <Pressable onPress={() => router.replace('/(auth)/register')}>
                <Text style={styles.linkText}>
                  Nu ai cont? <Text style={styles.link}>Înregistrează-te</Text>
                </Text>
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
  scroll: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 32,
    gap: 16,
  },
  logo: {
    fontSize: 36,
    fontWeight: '700',
    textAlign: 'center',
  },
  logoTailor: { color: Colors.textDark },
  logoBuy: { color: Colors.primary },
  subtitle: {
    fontSize: 16,
    color: Colors.textMid,
    textAlign: 'center',
    marginBottom: 8,
  },
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 24,
    padding: 24,
    gap: 16,
    shadowColor: Colors.cardShadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 5,
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
  button: {
    backgroundColor: Colors.buttonBg,
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 4,
  },
  buttonPressed: { opacity: 0.85 },
  buttonText: {
    color: Colors.buttonText,
    fontSize: 16,
    fontWeight: '700',
  },
  linkText: {
    textAlign: 'center',
    fontSize: 14,
    color: Colors.textMid,
  },
  link: {
    color: Colors.primary,
    fontWeight: '600',
  },
});
