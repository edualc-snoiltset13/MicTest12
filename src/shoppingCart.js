const DISCOUNT_CODES = {
  SAVE10: { type: 'percentage', value: 10 },
  SAVE20: { type: 'percentage', value: 20 },
  FLAT5: { type: 'fixed', value: 5 },
  FLAT15: { type: 'fixed', value: 15 },
  HALF: { type: 'percentage', value: 50 },
};

class ShoppingCart {
  constructor() {
    this.items = [];
    this.discountCode = null;
    this.checkedOut = false;
  }

  addItem(item) {
    if (this.checkedOut) {
      throw new Error('Cannot modify a checked-out cart');
    }
    if (!item || typeof item !== 'object') {
      throw new Error('Item must be an object');
    }
    if (!item.name || typeof item.name !== 'string') {
      throw new Error('Item must have a valid name');
    }
    if (typeof item.price !== 'number' || item.price < 0) {
      throw new Error('Item must have a non-negative price');
    }
    if (item.quantity !== undefined && (typeof item.quantity !== 'number' || item.quantity < 1 || !Number.isInteger(item.quantity))) {
      throw new Error('Item quantity must be a positive integer');
    }

    const qty = item.quantity || 1;
    const match = this.items.find(existing => existing.name === item.name);
    if (match) {
      match.quantity += qty;
    } else {
      this.items.push({ name: item.name, price: item.price, quantity: qty });
    }

    return this;
  }

  removeItem(name) {
    if (this.checkedOut) {
      throw new Error('Cannot modify a checked-out cart');
    }
    if (!name || typeof name !== 'string') {
      throw new Error('Item name must be a non-empty string');
    }

    const idx = this.items.findIndex(item => item.name === name);
    if (idx === -1) {
      throw new Error(`Item "${name}" not found in cart`);
    }

    this.items.splice(idx, 1);
    return this;
  }

  applyDiscount(code) {
    if (this.checkedOut) {
      throw new Error('Cannot modify a checked-out cart');
    }
    if (!code || typeof code !== 'string') {
      throw new Error('Discount code must be a non-empty string');
    }

    const normalized = code.toUpperCase();
    const discount = DISCOUNT_CODES[normalized];
    if (!discount) {
      throw new Error(`Invalid discount code: "${code}"`);
    }

    this.discountCode = { code: normalized, ...discount };
    return this;
  }

  getSubtotal() {
    return this.items.reduce((total, item) => total + item.price * item.quantity, 0);
  }

  getDiscount() {
    if (!this.discountCode) return 0;
    const subtotal = this.getSubtotal();

    if (this.discountCode.type === 'percentage') {
      return Math.round(subtotal * this.discountCode.value) / 100;
    }
    return Math.min(this.discountCode.value, subtotal);
  }

  calculateTotal() {
    const result = this.getSubtotal() - this.getDiscount();
    return Math.round(result * 100) / 100;
  }

  getItemCount() {
    return this.items.reduce((sum, item) => sum + item.quantity, 0);
  }

  checkout() {
    if (this.checkedOut) {
      throw new Error('Cart has already been checked out');
    }
    if (this.items.length === 0) {
      throw new Error('Cannot checkout an empty cart');
    }

    this.checkedOut = true;

    return {
      items: this.items.map(item => ({ ...item })),
      subtotal: this.getSubtotal(),
      discount: this.getDiscount(),
      total: this.calculateTotal(),
      itemCount: this.getItemCount(),
      discountCode: this.discountCode ? this.discountCode.code : null,
    };
  }
}

module.exports = { ShoppingCart, DISCOUNT_CODES };
