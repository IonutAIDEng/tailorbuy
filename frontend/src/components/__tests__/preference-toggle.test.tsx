import { fireEvent, render } from '@testing-library/react-native';
import React from 'react';

import { PreferenceToggle } from '../preference-toggle';

const noop = () => {};

describe('PreferenceToggle', () => {
  it('renders the label', () => {
    const { getByText } = render(
      <PreferenceToggle label="Doar numerar" value={false} onValueChange={noop} />,
    );
    expect(getByText('Doar numerar')).toBeTruthy();
  });

  it('reflects false value on the switch', () => {
    const { getByRole } = render(
      <PreferenceToggle label="Test" value={false} onValueChange={noop} />,
    );
    expect(getByRole('switch').props.value).toBe(false);
  });

  it('reflects true value on the switch', () => {
    const { getByRole } = render(
      <PreferenceToggle label="Test" value={true} onValueChange={noop} />,
    );
    expect(getByRole('switch').props.value).toBe(true);
  });

  it('calls onValueChange with true when toggled on', () => {
    const onValueChange = jest.fn();
    const { getByRole } = render(
      <PreferenceToggle label="Test" value={false} onValueChange={onValueChange} />,
    );
    fireEvent(getByRole('switch'), 'valueChange', true);
    expect(onValueChange).toHaveBeenCalledWith(true);
  });

  it('calls onValueChange with false when toggled off', () => {
    const onValueChange = jest.fn();
    const { getByRole } = render(
      <PreferenceToggle label="Test" value={true} onValueChange={onValueChange} />,
    );
    fireEvent(getByRole('switch'), 'valueChange', false);
    expect(onValueChange).toHaveBeenCalledWith(false);
  });

  it('calls onValueChange exactly once per toggle', () => {
    const onValueChange = jest.fn();
    const { getByRole } = render(
      <PreferenceToggle label="Test" value={false} onValueChange={onValueChange} />,
    );
    fireEvent(getByRole('switch'), 'valueChange', true);
    expect(onValueChange).toHaveBeenCalledTimes(1);
  });
});
