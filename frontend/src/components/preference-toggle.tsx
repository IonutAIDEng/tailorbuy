import { StyleSheet, Switch, Text, View } from 'react-native';

import { Colors } from '@/constants/colors';

interface PreferenceToggleProps {
  label: string;
  value: boolean;
  onValueChange: (value: boolean) => void;
}

export function PreferenceToggle({ label, value, onValueChange }: PreferenceToggleProps) {
  return (
    <View style={styles.card}>
      <Switch
        value={value}
        onValueChange={onValueChange}
        trackColor={{ false: Colors.toggleInactive, true: Colors.primaryLight }}
        thumbColor={value ? Colors.toggleActive : '#f4f3f4'}
        ios_backgroundColor={Colors.toggleInactive}
      />
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: Colors.cardBg,
    borderRadius: 16,
    paddingVertical: 16,
    paddingHorizontal: 12,
    alignItems: 'center',
    gap: 8,
    shadowColor: Colors.cardShadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },
  label: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.textDark,
    textAlign: 'center',
  },
});
