import React from 'react';
import { TouchableOpacity, View } from 'react-native';

const TRIGGER_VALUE = 123.7;

const Slider = ({ testID, onValueChange, value: _value, ...rest }: any) => (
  <View testID={testID ?? 'slider'} {...rest}>
    <TouchableOpacity
      testID={(testID ?? 'slider') + '-trigger'}
      onPress={() => onValueChange?.(TRIGGER_VALUE)}
    />
  </View>
);

export default Slider;
