import { cleanup, fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { Linking } from 'react-native';

import { ProductCard } from '../product-card';
import type { Product } from '@/types';

jest.mock('expo-image', () => {
  const ReactNative = require('react-native');
  return {
    Image: ({ testID }: any) => <ReactNative.View testID={testID} />,
  };
});

function makeProduct(overrides: Partial<Product> = {}): Product {
  return {
    id: 1,
    name: 'Televizor Samsung 55"',
    price_ron: 1299.99,
    rating: 4.7,
    review_count: 312,
    cash_on_delivery: true,
    store: 'eMAG',
    url: 'https://emag.ro/product/1',
    image_url: null,
    ...overrides,
  };
}

afterEach(cleanup);

describe('ProductCard', () => {
  describe('content rendering', () => {
    it('renders the product name', () => {
      const { getByText } = render(<ProductCard product={makeProduct()} />);
      expect(getByText('Televizor Samsung 55"')).toBeTruthy();
    });

    it('formats price without decimals', () => {
      const { getByText } = render(<ProductCard product={makeProduct({ price_ron: 1299.99 })} />);
      expect(getByText('1300 RON')).toBeTruthy();
    });

    it('formats integer price correctly', () => {
      const { getByText } = render(<ProductCard product={makeProduct({ price_ron: 500 })} />);
      expect(getByText('500 RON')).toBeTruthy();
    });

    it('renders the matches preferences indicator', () => {
      const { getByText } = render(<ProductCard product={makeProduct()} />);
      expect(getByText('Matches Preferences')).toBeTruthy();
    });
  });

  describe('store badge', () => {
    it.each([
      ['eMAG', 'eMAG'],
      ['emag', 'eMAG'],
      ['altex', 'ALTEX'],
      ['ALTEX', 'ALTEX'],
    ])('renders correct label for store "%s"', (store, expectedLabel) => {
      const { getByText } = render(<ProductCard product={makeProduct({ store })} />);
      expect(getByText(expectedLabel)).toBeTruthy();
    });

    it('renders unknown store name as-is', () => {
      const { getByText } = render(<ProductCard product={makeProduct({ store: 'Flanco' })} />);
      expect(getByText('Flanco')).toBeTruthy();
    });
  });

  describe('press interaction', () => {
    it('opens the product URL on press', () => {
      const spy = jest.spyOn(Linking, 'openURL').mockResolvedValue(undefined);
      const product = makeProduct({ url: 'https://emag.ro/product/1' });
      const { getByTestId, unmount } = render(<ProductCard product={product} />);
      fireEvent.press(getByTestId('product-card-pressable'));
      expect(spy).toHaveBeenCalledWith('https://emag.ro/product/1');
      unmount();
      spy.mockRestore();
    });

    it('does not call Linking when url is empty string', () => {
      const spy = jest.spyOn(Linking, 'openURL').mockResolvedValue(undefined);
      const product = makeProduct({ url: '' });
      const { getByTestId, unmount } = render(<ProductCard product={product} />);
      fireEvent.press(getByTestId('product-card-pressable'));
      expect(spy).not.toHaveBeenCalled();
      unmount();
      spy.mockRestore();
    });
  });
});
