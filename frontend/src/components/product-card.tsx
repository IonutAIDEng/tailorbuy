import { Image } from 'expo-image';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';

import { Colors } from '@/constants/colors';
import { StoreBadge } from '@/components/store-badge';
import type { Product } from '@/types';

interface ProductCardProps {
  product: Product;
}

const MATCH_CONFIG = {
  all: {
    label: '✓ Preferințe bifate',
    color: Colors.matchesGreen,
    bg: '#dcfce7',
  },
  partial: {
    label: '~ Potrivire parțială',
    color: Colors.matchesAmber,
    bg: '#fef3c7',
  },
} as const;

export function ProductCard({ product }: ProductCardProps) {
  const handlePress = () => {
    if (product.url) {
      Linking.openURL(product.url);
    }
  };

  const match = MATCH_CONFIG[product.status_match ?? 'all'];

  return (
    <Pressable testID="product-card-pressable" style={({ pressed }) => [styles.card, pressed && styles.pressed]} onPress={handlePress}>
      <Image
        source={product.image_url ?? undefined}
        style={styles.image}
        contentFit="cover"
        placeholder={{ uri: undefined }}
      />

      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={2}>
          {product.name}
        </Text>

        <Text style={styles.price}>{product.price_ron.toFixed(0)} RON</Text>

        <StoreBadge store={product.store} />

        <View style={[styles.matchBadge, { backgroundColor: match.bg }]}>
          <Text style={[styles.matchText, { color: match.color }]}>
            {match.label}
          </Text>
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    padding: 12,
    gap: 14,
    shadowColor: Colors.cardShadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 8,
    elevation: 3,
    marginHorizontal: 16,
  },
  pressed: {
    opacity: 0.85,
  },
  image: {
    width: 100,
    height: 100,
    borderRadius: 12,
    backgroundColor: Colors.border,
  },
  info: {
    flex: 1,
    gap: 6,
    justifyContent: 'center',
  },
  name: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textDark,
    lineHeight: 20,
  },
  price: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textDark,
  },
  matchBadge: {
    alignSelf: 'flex-start',
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
    marginTop: 2,
  },
  matchText: {
    fontSize: 11,
    fontWeight: '600',
  },
});
