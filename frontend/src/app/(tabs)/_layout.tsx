import { Tabs } from 'expo-router';
import { StyleSheet, Text } from 'react-native';

import { Colors } from '@/constants/colors';

function TabIcon({ focused, label }: { focused: boolean; label: string }) {
  return (
    <Text style={[styles.icon, focused ? styles.iconActive : styles.iconInactive]}>
      {label}
    </Text>
  );
}

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: Colors.tabIconActive,
        tabBarInactiveTintColor: Colors.tabIconInactive,
        tabBarLabelStyle: styles.tabLabel,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Căutare',
          tabBarIcon: ({ focused }) => <TabIcon focused={focused} label="🔍" />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profil',
          tabBarIcon: ({ focused }) => <TabIcon focused={focused} label="👤" />,
        }}
      />
      <Tabs.Screen
        name="deals"
        options={{
          title: 'Oferte',
          tabBarIcon: ({ focused }) => <TabIcon focused={focused} label="🏷️" />,
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: Colors.tabBar,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    height: 60,
    paddingBottom: 8,
    paddingTop: 4,
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: '500',
  },
  icon: {
    fontSize: 20,
  },
  iconActive: {
    opacity: 1,
  },
  iconInactive: {
    opacity: 0.5,
  },
});
