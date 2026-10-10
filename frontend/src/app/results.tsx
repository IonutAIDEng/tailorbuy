import { router, useLocalSearchParams } from 'expo-router';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { GradientBackground } from '@/components/gradient-background';
import { ProductCard } from '@/components/product-card';
import { Colors } from '@/constants/colors';
import type { Product } from '@/types';

export default function ResultsScreen() {
  const { query, products: productsParam, total, message } = useLocalSearchParams<{
    query: string;
    products: string;
    total: string;
    message: string;
  }>();

  const products: Product[] = productsParam ? JSON.parse(productsParam) : [];

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safe}>
        <View style={styles.header}>
          <Pressable onPress={() => router.back()} style={styles.backButton}>
            <Text style={styles.backIcon}>←</Text>
          </Pressable>
          <View style={styles.headerText}>
            <Text style={styles.headerTitle}>Rezultate căutare</Text>
            <Text style={styles.headerSubtitle}>
              {total} produse pentru &quot;{query}&quot;
            </Text>
          </View>
        </View>

        {products.length === 0 ? (
          <View style={styles.emptyContainer}>
            <View style={styles.emptyCard}>
              <Text style={styles.emptyEmoji}>🔍</Text>
              <Text style={styles.emptyTitle}>Niciun rezultat</Text>
              <Text style={styles.emptyText}>
                {message || 'Nu am găsit produse pentru această căutare. Încearcă cu alți termeni.'}
              </Text>
            </View>
          </View>
        ) : (
          <FlatList
            data={products}
            keyExtractor={(item) => String(item.id)}
            renderItem={({ item }) => <ProductCard product={item} />}
            contentContainerStyle={styles.list}
            showsVerticalScrollIndicator={false}
            ItemSeparatorComponent={() => <View style={styles.separator} />}
          />
        )}
      </SafeAreaView>
    </GradientBackground>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
    gap: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.cardBg,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.cardShadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },
  backIcon: {
    fontSize: 20,
    color: Colors.textDark,
    fontWeight: '600',
  },
  headerText: { flex: 1 },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.textDark,
  },
  headerSubtitle: {
    fontSize: 12,
    color: Colors.textMid,
    marginTop: 2,
  },
  list: {
    paddingTop: 8,
    paddingBottom: 24,
  },
  separator: { height: 12 },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  emptyCard: {
    backgroundColor: Colors.cardBg,
    borderRadius: 24,
    padding: 32,
    alignItems: 'center',
    gap: 12,
  },
  emptyEmoji: { fontSize: 40 },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.textDark,
  },
  emptyText: {
    fontSize: 14,
    color: Colors.textMid,
    textAlign: 'center',
    lineHeight: 22,
  },
});
