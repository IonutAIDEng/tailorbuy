import { fireEvent, render } from '@testing-library/react-native';
import React from 'react';

import { PriceSliderInput } from '../price-slider-input';

const noop = () => {};

function doubleTap(element: Parameters<typeof fireEvent.press>[0]) {
  jest.spyOn(Date, 'now')
    .mockReturnValueOnce(1000)
    .mockReturnValueOnce(1200); // 200ms apart — within 350ms window
  fireEvent.press(element);
  fireEvent.press(element);
}

function openInput(initialValue = 0) {
  const onChange = jest.fn();
  const utils = render(<PriceSliderInput value={initialValue} onChange={onChange} />);
  doubleTap(utils.getByTestId('price-value-tap'));
  return { ...utils, onChange };
}

describe('PriceSliderInput', () => {
  afterEach(() => jest.restoreAllMocks());

  describe('display', () => {
    it('renders the label "Preț maxim"', () => {
      const { getByText } = render(<PriceSliderInput value={0} onChange={noop} />);
      expect(getByText('Preț maxim')).toBeTruthy();
    });

    it('shows "Orice preț" when value is 0', () => {
      const { getByText } = render(<PriceSliderInput value={0} onChange={noop} />);
      expect(getByText('Orice preț')).toBeTruthy();
    });

    it('shows formatted value when non-zero', () => {
      const { getByText } = render(<PriceSliderInput value={500} onChange={noop} />);
      expect(getByText('500 RON')).toBeTruthy();
    });

    it('renders the slider element', () => {
      const { getByTestId } = render(<PriceSliderInput value={100} onChange={noop} />);
      expect(getByTestId('slider')).toBeTruthy();
    });

    it('renders the minimum range label "0"', () => {
      const { getAllByText } = render(<PriceSliderInput value={0} onChange={noop} />);
      expect(getAllByText('0').length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('double-tap to edit', () => {
    it('does not open input on single tap', () => {
      jest.spyOn(Date, 'now').mockReturnValue(1000);
      const { getByTestId, queryByPlaceholderText } = render(
        <PriceSliderInput value={0} onChange={noop} />,
      );
      fireEvent.press(getByTestId('price-value-tap'));
      expect(queryByPlaceholderText('0')).toBeNull();
    });

    it('opens input on double tap within 350ms', () => {
      const { getByTestId, getByPlaceholderText } = render(
        <PriceSliderInput value={0} onChange={noop} />,
      );
      doubleTap(getByTestId('price-value-tap'));
      expect(getByPlaceholderText('0')).toBeTruthy();
    });

    it('does not open input when taps are more than 350ms apart', () => {
      jest.spyOn(Date, 'now')
        .mockReturnValueOnce(1000)
        .mockReturnValueOnce(1500); // 500ms gap
      const { getByTestId, queryByPlaceholderText } = render(
        <PriceSliderInput value={0} onChange={noop} />,
      );
      fireEvent.press(getByTestId('price-value-tap'));
      fireEvent.press(getByTestId('price-value-tap'));
      expect(queryByPlaceholderText('0')).toBeNull();
    });

    it('pre-fills with empty string when current value is 0', () => {
      const { getByTestId, getByPlaceholderText } = render(
        <PriceSliderInput value={0} onChange={noop} />,
      );
      doubleTap(getByTestId('price-value-tap'));
      expect(getByPlaceholderText('0').props.value).toBe('');
    });

    it('pre-fills with current value when non-zero', () => {
      const { getByTestId, getByDisplayValue } = render(
        <PriceSliderInput value={300} onChange={noop} />,
      );
      doubleTap(getByTestId('price-value-tap'));
      expect(getByDisplayValue('300')).toBeTruthy();
    });
  });

  describe('input — digit filtering', () => {
    it('strips non-numeric characters', () => {
      const { getByPlaceholderText } = openInput();
      fireEvent.changeText(getByPlaceholderText('0'), 'abc123');
      expect(getByPlaceholderText('0').props.value).toBe('123');
    });

    it('clears the error when the user types after an error', () => {
      const { getByPlaceholderText, queryByText } = openInput();
      fireEvent.changeText(getByPlaceholderText('0'), '99999');
      fireEvent(getByPlaceholderText('0'), 'submitEditing');
      // error is shown — now type again
      fireEvent.changeText(getByPlaceholderText('0'), '300');
      expect(queryByText('Maximum 10000 RON')).toBeNull();
    });
  });

  describe('input — submit (Enter key)', () => {
    it('calls onChange with parsed integer on valid submit', () => {
      const { getByPlaceholderText, onChange } = openInput();
      fireEvent.changeText(getByPlaceholderText('0'), '500');
      fireEvent(getByPlaceholderText('0'), 'submitEditing');
      expect(onChange).toHaveBeenCalledWith(500);
    });

    it('calls onChange with 0 when input is empty on submit', () => {
      const { getByPlaceholderText, onChange } = openInput();
      fireEvent.changeText(getByPlaceholderText('0'), '');
      fireEvent(getByPlaceholderText('0'), 'submitEditing');
      expect(onChange).toHaveBeenCalledWith(0);
    });

    it('calls onChange with 0 when input is "0" on submit', () => {
      const { getByPlaceholderText, onChange } = openInput();
      fireEvent.changeText(getByPlaceholderText('0'), '0');
      fireEvent(getByPlaceholderText('0'), 'submitEditing');
      expect(onChange).toHaveBeenCalledWith(0);
    });

    it('shows error when submitted value exceeds 10000', () => {
      const { getByPlaceholderText, getByText } = openInput();
      fireEvent.changeText(getByPlaceholderText('0'), '99999');
      fireEvent(getByPlaceholderText('0'), 'submitEditing');
      expect(getByText('Maximum 10000 RON')).toBeTruthy();
    });

    it('does not call onChange when submitted value exceeds max', () => {
      const { getByPlaceholderText, onChange } = openInput();
      fireEvent.changeText(getByPlaceholderText('0'), '99999');
      fireEvent(getByPlaceholderText('0'), 'submitEditing');
      expect(onChange).not.toHaveBeenCalled();
    });

    it('hides the input after a successful submit', () => {
      const { getByPlaceholderText, queryByPlaceholderText } = openInput();
      fireEvent.changeText(getByPlaceholderText('0'), '200');
      fireEvent(getByPlaceholderText('0'), 'submitEditing');
      expect(queryByPlaceholderText('0')).toBeNull();
    });
  });

  describe('input — blur', () => {
    it('saves valid value on blur', () => {
      const { getByPlaceholderText, onChange } = openInput();
      fireEvent.changeText(getByPlaceholderText('0'), '400');
      fireEvent(getByPlaceholderText('0'), 'blur');
      expect(onChange).toHaveBeenCalledWith(400);
    });

    it('resets to 0 on blur when input is empty', () => {
      const { getByPlaceholderText, onChange } = openInput(200);
      fireEvent.changeText(getByPlaceholderText('0'), '');
      fireEvent(getByPlaceholderText('0'), 'blur');
      expect(onChange).toHaveBeenCalledWith(0);
    });

    it('resets to 0 on blur when input is "0"', () => {
      const { getByPlaceholderText, onChange } = openInput(200);
      fireEvent.changeText(getByPlaceholderText('0'), '0');
      fireEvent(getByPlaceholderText('0'), 'blur');
      expect(onChange).toHaveBeenCalledWith(0);
    });

    it('does not call onChange on blur when value exceeds maximum', () => {
      const { getByPlaceholderText, onChange } = openInput();
      fireEvent.changeText(getByPlaceholderText('0'), '99999');
      fireEvent(getByPlaceholderText('0'), 'blur');
      expect(onChange).not.toHaveBeenCalled();
    });

    it('hides the input after blur', () => {
      const { getByPlaceholderText, queryByPlaceholderText } = openInput();
      fireEvent(getByPlaceholderText('0'), 'blur');
      expect(queryByPlaceholderText('0')).toBeNull();
    });
  });

  describe('slider', () => {
    it('rounds the slider float value before calling onChange', () => {
      const onChange = jest.fn();
      const { getByTestId } = render(<PriceSliderInput value={0} onChange={onChange} />);
      // Mock fires 123.7 → Math.round → 124
      fireEvent.press(getByTestId('slider-trigger'));
      expect(onChange).toHaveBeenCalledWith(124);
    });
  });
});
