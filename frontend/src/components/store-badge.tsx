import { StyleSheet, Text, View } from 'react-native';

import { Colors } from '@/constants/colors';

interface StoreBadgeProps {
  store: string;
}

const STORE_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  emag: { bg: Colors.emagRed, text: '#ffffff', label: 'eMAG' },
  altex: { bg: Colors.altexYellow, text: Colors.altexRed, label: 'ALTEX' },
};

function normalise(store: string) {
  return store.toLowerCase().replace(/[^a-z]/g, '');
}

export function StoreBadge({ store }: StoreBadgeProps) {
  const config = STORE_STYLES[normalise(store)];

  if (config) {
    return (
      <View style={[styles.badge, { backgroundColor: config.bg }]}>
        <Text style={[styles.text, { color: config.text }]}>{config.label}</Text>
      </View>
    );
  }

  return (
    <View style={[styles.badge, styles.fallback]}>
      <Text style={[styles.text, { color: Colors.textDark }]}>{store}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  fallback: {
    backgroundColor: Colors.border,
  },
  text: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
});
