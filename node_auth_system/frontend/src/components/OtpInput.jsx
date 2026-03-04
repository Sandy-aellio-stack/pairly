import React from 'react';

const OtpInput = ({ value, onChange, length = 6 }) => {
    const handleChange = (e, index) => {
        const val = e.target.value.replace(/[^0-9]/g, '');
        if (!val) return;

        const newValue = value.split('');
        newValue[index] = val.slice(-1);
        const updatedValue = newValue.join('');
        onChange(updatedValue);

        // Auto-focus next input
        if (index < length - 1) {
            e.target.nextSibling?.focus();
        }
    };

    const handleKeyDown = (e, index) => {
        if (e.key === 'Backspace' && !value[index] && index > 0) {
            e.target.previousSibling?.focus();
        }
    };

    return (
        <div className="flex gap-2 justify-center">
            {Array.from({ length }).map((_, i) => (
                <input
                    key={i}
                    type="text"
                    maxLength={1}
                    value={value[i] || ''}
                    onChange={(e) => handleChange(e, i)}
                    onKeyDown={(e) => handleKeyDown(e, i)}
                    className="w-10 h-12 text-center text-xl border-2 rounded-lg focus:border-blue-500 focus:outline-none transition-colors"
                />
            ))}
        </div>
    );
};

export default OtpInput;
