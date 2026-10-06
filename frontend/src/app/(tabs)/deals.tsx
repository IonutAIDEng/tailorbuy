import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { GradientBackground } from '@/components/gradient-background';
import { Colors } from '@/constants/colors';

export default function DealsScreen() {
  return (
    <GradientBackground>
      <SafeAreaView style={styles.safe}>
        <View style={styles.container}>
          <View style={styles.card}>
            <Text style={styles.emoji}>🏷️</Text>
            <Text style={styles.title}>Oferte în curând</Text>
            <Text style={styles.subtitle}>
              Oferte personalizate și reduceri exclusiviste vor apărea aici într-o versiune viitoare.
            </Text>
          </View>
        </View>
      </SafeAreaView>
    </GradientBackground>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  container: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: 24,
    padding: 32,
    alignItems: 'center',
    gap: 16,
    shadowColor: Colors.cardShadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 16,
    elevation: 5,
  },
  emoji: { fontSize: 48 },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: Colors.textDark,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: Colors.textMid,
    textAlign: 'center',
    lineHeight: 22,
  },
});
