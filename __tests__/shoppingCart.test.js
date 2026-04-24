const { ShoppingCart, DISCOUNT_CODES } = require('../src/shoppingCart');

describe('ShoppingCart', () => {
  let cart;

  beforeEach(() => {
    cart = new ShoppingCart();
  });

  // ── Constructor ───────────────────────────────────────────────────────

  describe('initial state', () => {
    it('starts with an empty items list', () => {
      expect(cart.items).toEqual([]);
    });

    it('has no discount applied', () => {
      expect(cart.discountCode).toBeNull();
    });

    it('is not checked out', () => {
      expect(cart.checkedOut).toBe(false);
    });
  });

  // ── addItem ───────────────────────────────────────────────────────────

  describe('addItem', () => {
    it('adds an item with default quantity of 1', () => {
      cart.addItem({ name: 'Milk', price: 3.49 });
      expect(cart.items).toEqual([{ name: 'Milk', price: 3.49, quantity: 1 }]);
    });

    it('respects an explicit quantity', () => {
      cart.addItem({ name: 'Eggs', price: 2.99, quantity: 2 });
      expect(cart.items[0].quantity).toBe(2);
    });

    it('merges quantity when the same item is added again', () => {
      cart.addItem({ name: 'Bread', price: 4.0 });
      cart.addItem({ name: 'Bread', price: 4.0, quantity: 3 });
      expect(cart.items).toHaveLength(1);
      expect(cart.items[0].quantity).toBe(4);
    });

    it('keeps different items separate', () => {
      cart.addItem({ name: 'A', price: 1 });
      cart.addItem({ name: 'B', price: 2 });
      cart.addItem({ name: 'C', price: 3 });
      expect(cart.items).toHaveLength(3);
    });

    it('accepts a zero price', () => {
      cart.addItem({ name: 'Freebie', price: 0 });
      expect(cart.items[0].price).toBe(0);
    });

    it('returns the cart for chaining', () => {
      const result = cart.addItem({ name: 'X', price: 5 });
      expect(result).toBe(cart);
    });

    it('supports fluent chaining of multiple adds', () => {
      cart.addItem({ name: 'X', price: 1 }).addItem({ name: 'Y', price: 2 });
      expect(cart.items).toHaveLength(2);
    });

    it('rejects null', () => {
      expect(() => cart.addItem(null)).toThrow('Item must be an object');
    });

    it('rejects undefined', () => {
      expect(() => cart.addItem(undefined)).toThrow('Item must be an object');
    });

    it('rejects a primitive string', () => {
      expect(() => cart.addItem('thing')).toThrow('Item must be an object');
    });

    it('rejects a missing name', () => {
      expect(() => cart.addItem({ price: 5 })).toThrow('Item must have a valid name');
    });

    it('rejects an empty-string name', () => {
      expect(() => cart.addItem({ name: '', price: 5 })).toThrow('Item must have a valid name');
    });

    it('rejects a numeric name', () => {
      expect(() => cart.addItem({ name: 42, price: 5 })).toThrow('Item must have a valid name');
    });

    it('rejects a missing price', () => {
      expect(() => cart.addItem({ name: 'X' })).toThrow('Item must have a non-negative price');
    });

    it('rejects a negative price', () => {
      expect(() => cart.addItem({ name: 'X', price: -10 })).toThrow('Item must have a non-negative price');
    });

    it('rejects a string price', () => {
      expect(() => cart.addItem({ name: 'X', price: '5' })).toThrow('Item must have a non-negative price');
    });

    it('rejects zero quantity', () => {
      expect(() => cart.addItem({ name: 'X', price: 5, quantity: 0 })).toThrow('Item quantity must be a positive integer');
    });

    it('rejects negative quantity', () => {
      expect(() => cart.addItem({ name: 'X', price: 5, quantity: -2 })).toThrow('Item quantity must be a positive integer');
    });

    it('rejects fractional quantity', () => {
      expect(() => cart.addItem({ name: 'X', price: 5, quantity: 1.7 })).toThrow('Item quantity must be a positive integer');
    });

    it('rejects adds on a checked-out cart', () => {
      cart.addItem({ name: 'X', price: 5 }).checkout();
      expect(() => cart.addItem({ name: 'Y', price: 3 })).toThrow('Cannot modify a checked-out cart');
    });
  });

  // ── removeItem ────────────────────────────────────────────────────────

  describe('removeItem', () => {
    beforeEach(() => {
      cart
        .addItem({ name: 'Alpha', price: 10 })
        .addItem({ name: 'Beta', price: 20 })
        .addItem({ name: 'Gamma', price: 30 });
    });

    it('removes an item by name', () => {
      cart.removeItem('Beta');
      expect(cart.items).toHaveLength(2);
      expect(cart.items.find(i => i.name === 'Beta')).toBeUndefined();
    });

    it('keeps remaining items in order', () => {
      cart.removeItem('Beta');
      expect(cart.items.map(i => i.name)).toEqual(['Alpha', 'Gamma']);
    });

    it('returns the cart for chaining', () => {
      expect(cart.removeItem('Alpha')).toBe(cart);
    });

    it('can empty the cart completely', () => {
      cart.removeItem('Alpha').removeItem('Beta').removeItem('Gamma');
      expect(cart.items).toHaveLength(0);
    });

    it('throws for an item not in the cart', () => {
      expect(() => cart.removeItem('Delta')).toThrow('Item "Delta" not found in cart');
    });

    it('throws when removing the same item twice', () => {
      cart.removeItem('Alpha');
      expect(() => cart.removeItem('Alpha')).toThrow('Item "Alpha" not found in cart');
    });

    it('rejects null name', () => {
      expect(() => cart.removeItem(null)).toThrow('Item name must be a non-empty string');
    });

    it('rejects empty string name', () => {
      expect(() => cart.removeItem('')).toThrow('Item name must be a non-empty string');
    });

    it('rejects non-string name', () => {
      expect(() => cart.removeItem(99)).toThrow('Item name must be a non-empty string');
    });

    it('rejects removal on a checked-out cart', () => {
      cart.checkout();
      expect(() => cart.removeItem('Alpha')).toThrow('Cannot modify a checked-out cart');
    });

    it('chains remove into add', () => {
      cart.removeItem('Alpha').addItem({ name: 'Omega', price: 50 });
      expect(cart.items.map(i => i.name)).toEqual(['Beta', 'Gamma', 'Omega']);
    });
  });

  // ── applyDiscount ─────────────────────────────────────────────────────

  describe('applyDiscount', () => {
    it('stores a percentage discount', () => {
      cart.applyDiscount('SAVE10');
      expect(cart.discountCode).toEqual({ code: 'SAVE10', type: 'percentage', value: 10 });
    });

    it('stores a fixed discount', () => {
      cart.applyDiscount('FLAT5');
      expect(cart.discountCode).toEqual({ code: 'FLAT5', type: 'fixed', value: 5 });
    });

    it('normalizes lowercase input', () => {
      cart.applyDiscount('save20');
      expect(cart.discountCode.code).toBe('SAVE20');
    });

    it('normalizes mixed-case input', () => {
      cart.applyDiscount('Half');
      expect(cart.discountCode.code).toBe('HALF');
    });

    it('replaces a previous discount', () => {
      cart.applyDiscount('SAVE10');
      cart.applyDiscount('FLAT15');
      expect(cart.discountCode.code).toBe('FLAT15');
    });

    it('returns the cart for chaining', () => {
      expect(cart.applyDiscount('SAVE10')).toBe(cart);
    });

    it('rejects an unknown code', () => {
      expect(() => cart.applyDiscount('NOPE')).toThrow('Invalid discount code: "NOPE"');
    });

    it('rejects null', () => {
      expect(() => cart.applyDiscount(null)).toThrow('Discount code must be a non-empty string');
    });

    it('rejects empty string', () => {
      expect(() => cart.applyDiscount('')).toThrow('Discount code must be a non-empty string');
    });

    it('rejects non-string', () => {
      expect(() => cart.applyDiscount(100)).toThrow('Discount code must be a non-empty string');
    });

    it('rejects discount on a checked-out cart', () => {
      cart.addItem({ name: 'X', price: 10 }).checkout();
      expect(() => cart.applyDiscount('SAVE10')).toThrow('Cannot modify a checked-out cart');
    });
  });

  // ── getSubtotal ───────────────────────────────────────────────────────

  describe('getSubtotal', () => {
    it('is 0 for an empty cart', () => {
      expect(cart.getSubtotal()).toBe(0);
    });

    it('multiplies price by quantity', () => {
      cart.addItem({ name: 'Widget', price: 7.5, quantity: 4 });
      expect(cart.getSubtotal()).toBe(30);
    });

    it('sums across multiple items', () => {
      cart.addItem({ name: 'A', price: 3, quantity: 2 });
      cart.addItem({ name: 'B', price: 5, quantity: 1 });
      expect(cart.getSubtotal()).toBe(11);
    });
  });

  // ── getDiscount ───────────────────────────────────────────────────────

  describe('getDiscount', () => {
    it('is 0 with no code', () => {
      cart.addItem({ name: 'X', price: 50 });
      expect(cart.getDiscount()).toBe(0);
    });

    it('computes percentage correctly', () => {
      cart.addItem({ name: 'X', price: 200 });
      cart.applyDiscount('SAVE20');
      expect(cart.getDiscount()).toBe(40);
    });

    it('returns fixed amount when subtotal is larger', () => {
      cart.addItem({ name: 'X', price: 100 });
      cart.applyDiscount('FLAT15');
      expect(cart.getDiscount()).toBe(15);
    });

    it('caps fixed discount at the subtotal', () => {
      cart.addItem({ name: 'X', price: 3 });
      cart.applyDiscount('FLAT5');
      expect(cart.getDiscount()).toBe(3);
    });

    it('is 0 on an empty cart even with a code', () => {
      cart.applyDiscount('HALF');
      expect(cart.getDiscount()).toBe(0);
    });
  });

  // ── calculateTotal ────────────────────────────────────────────────────

  describe('calculateTotal', () => {
    it('is 0 for an empty cart', () => {
      expect(cart.calculateTotal()).toBe(0);
    });

    it('equals item price for a single item', () => {
      cart.addItem({ name: 'Pen', price: 1.29 });
      expect(cart.calculateTotal()).toBe(1.29);
    });

    it('sums multiple items', () => {
      cart.addItem({ name: 'A', price: 5.5 });
      cart.addItem({ name: 'B', price: 4.5 });
      expect(cart.calculateTotal()).toBe(10);
    });

    it('factors in quantity', () => {
      cart.addItem({ name: 'Tile', price: 1.25, quantity: 4 });
      expect(cart.calculateTotal()).toBe(5);
    });

    it('subtracts 10% discount', () => {
      cart.addItem({ name: 'Jacket', price: 80 });
      cart.applyDiscount('SAVE10');
      expect(cart.calculateTotal()).toBe(72);
    });

    it('subtracts 20% discount', () => {
      cart.addItem({ name: 'Jacket', price: 80 });
      cart.applyDiscount('SAVE20');
      expect(cart.calculateTotal()).toBe(64);
    });

    it('subtracts 50% discount', () => {
      cart.addItem({ name: 'Jacket', price: 80 });
      cart.applyDiscount('HALF');
      expect(cart.calculateTotal()).toBe(40);
    });

    it('subtracts fixed $5 discount', () => {
      cart.addItem({ name: 'Hat', price: 25 });
      cart.applyDiscount('FLAT5');
      expect(cart.calculateTotal()).toBe(20);
    });

    it('subtracts fixed $15 discount', () => {
      cart.addItem({ name: 'Hat', price: 25 });
      cart.applyDiscount('FLAT15');
      expect(cart.calculateTotal()).toBe(10);
    });

    it('floors at 0 when fixed discount exceeds subtotal', () => {
      cart.addItem({ name: 'Sticker', price: 2 });
      cart.applyDiscount('FLAT15');
      expect(cart.calculateTotal()).toBe(0);
    });

    it('handles percentage on multi-item quantities', () => {
      cart.addItem({ name: 'A', price: 2, quantity: 5 });
      cart.addItem({ name: 'B', price: 3, quantity: 2 });
      cart.applyDiscount('SAVE10');
      expect(cart.calculateTotal()).toBe(14.4);
    });

    it('rounds to two decimal places', () => {
      cart.addItem({ name: 'Gizmo', price: 10.33 });
      cart.applyDiscount('SAVE10');
      expect(cart.calculateTotal()).toBeCloseTo(9.3, 2);
    });

    it('returns full total when no discount is set', () => {
      cart.addItem({ name: 'A', price: 15 });
      cart.addItem({ name: 'B', price: 25 });
      expect(cart.calculateTotal()).toBe(40);
    });
  });

  // ── getItemCount ──────────────────────────────────────────────────────

  describe('getItemCount', () => {
    it('is 0 for an empty cart', () => {
      expect(cart.getItemCount()).toBe(0);
    });

    it('counts a single item', () => {
      cart.addItem({ name: 'Solo', price: 9 });
      expect(cart.getItemCount()).toBe(1);
    });

    it('sums quantities across items', () => {
      cart.addItem({ name: 'A', price: 1, quantity: 3 });
      cart.addItem({ name: 'B', price: 2, quantity: 7 });
      expect(cart.getItemCount()).toBe(10);
    });

    it('includes merged duplicates', () => {
      cart.addItem({ name: 'A', price: 1, quantity: 2 });
      cart.addItem({ name: 'A', price: 1, quantity: 3 });
      expect(cart.getItemCount()).toBe(5);
    });
  });

  // ── checkout ──────────────────────────────────────────────────────────

  describe('checkout', () => {
    it('returns a complete order summary', () => {
      cart.addItem({ name: 'Shoe', price: 60, quantity: 2 });
      const order = cart.checkout();
      expect(order).toEqual({
        items: [{ name: 'Shoe', price: 60, quantity: 2 }],
        subtotal: 120,
        discount: 0,
        total: 120,
        itemCount: 2,
        discountCode: null,
      });
    });

    it('includes discount details when a code is applied', () => {
      cart.addItem({ name: 'Watch', price: 250 }).applyDiscount('SAVE20');
      const order = cart.checkout();
      expect(order).toEqual({
        items: [{ name: 'Watch', price: 250, quantity: 1 }],
        subtotal: 250,
        discount: 50,
        total: 200,
        itemCount: 1,
        discountCode: 'SAVE20',
      });
    });

    it('returns copied items, not references', () => {
      cart.addItem({ name: 'Mug', price: 12 });
      const order = cart.checkout();
      order.items[0].name = 'TAMPERED';
      expect(cart.items[0].name).toBe('Mug');
    });

    it('sets the checkedOut flag', () => {
      cart.addItem({ name: 'X', price: 1 });
      cart.checkout();
      expect(cart.checkedOut).toBe(true);
    });

    it('throws on an empty cart', () => {
      expect(() => cart.checkout()).toThrow('Cannot checkout an empty cart');
    });

    it('throws on double checkout', () => {
      cart.addItem({ name: 'X', price: 1 });
      cart.checkout();
      expect(() => cart.checkout()).toThrow('Cart has already been checked out');
    });

    it('blocks addItem after checkout', () => {
      cart.addItem({ name: 'X', price: 1 }).checkout();
      expect(() => cart.addItem({ name: 'Y', price: 2 })).toThrow('Cannot modify a checked-out cart');
    });

    it('blocks removeItem after checkout', () => {
      cart.addItem({ name: 'X', price: 1 }).checkout();
      expect(() => cart.removeItem('X')).toThrow('Cannot modify a checked-out cart');
    });

    it('blocks applyDiscount after checkout', () => {
      cart.addItem({ name: 'X', price: 1 }).checkout();
      expect(() => cart.applyDiscount('SAVE10')).toThrow('Cannot modify a checked-out cart');
    });

    it('handles a complex real-world order', () => {
      cart
        .addItem({ name: 'Laptop', price: 999.99 })
        .addItem({ name: 'Mouse', price: 29.99, quantity: 2 })
        .addItem({ name: 'Cable', price: 9.99, quantity: 3 })
        .applyDiscount('SAVE10');

      const order = cart.checkout();
      expect(order.items).toHaveLength(3);
      expect(order.itemCount).toBe(6);
      expect(order.subtotal).toBeCloseTo(1089.94, 2);
      expect(order.discount).toBeCloseTo(108.99, 1);
      expect(order.total).toBeCloseTo(order.subtotal - order.discount, 2);
      expect(order.discountCode).toBe('SAVE10');
    });
  });

  // ── End-to-end workflows ──────────────────────────────────────────────

  describe('end-to-end workflows', () => {
    it('add → discount → checkout', () => {
      cart.addItem({ name: 'Book', price: 12.99 });
      cart.addItem({ name: 'Pen', price: 1.99, quantity: 5 });
      cart.applyDiscount('FLAT5');

      expect(cart.getItemCount()).toBe(6);
      expect(cart.getSubtotal()).toBeCloseTo(22.94, 2);
      expect(cart.checkout().total).toBeCloseTo(17.94, 2);
    });

    it('add → remove → checkout', () => {
      cart.addItem({ name: 'A', price: 10 });
      cart.addItem({ name: 'B', price: 20 });
      cart.addItem({ name: 'C', price: 30 });
      cart.removeItem('B');

      const order = cart.checkout();
      expect(order.items).toHaveLength(2);
      expect(order.total).toBe(40);
    });

    it('swap discount codes before checkout', () => {
      cart.addItem({ name: 'Item', price: 100 });
      cart.applyDiscount('SAVE10');
      expect(cart.calculateTotal()).toBe(90);

      cart.applyDiscount('SAVE20');
      expect(cart.calculateTotal()).toBe(80);

      const order = cart.checkout();
      expect(order.total).toBe(80);
      expect(order.discountCode).toBe('SAVE20');
    });

    it('independent carts do not share state', () => {
      const other = new ShoppingCart();
      cart.addItem({ name: 'A', price: 10 });
      other.addItem({ name: 'B', price: 20 });

      expect(cart.items).toHaveLength(1);
      expect(other.items).toHaveLength(1);
      expect(cart.items[0].name).toBe('A');
      expect(other.items[0].name).toBe('B');
    });

    it('full fluent chain through checkout', () => {
      const order = cart
        .addItem({ name: 'A', price: 10 })
        .addItem({ name: 'B', price: 20, quantity: 2 })
        .addItem({ name: 'C', price: 5 })
        .removeItem('C')
        .applyDiscount('SAVE10')
        .checkout();

      expect(order.total).toBe(45);
    });
  });

  // ── DISCOUNT_CODES export ─────────────────────────────────────────────

  describe('DISCOUNT_CODES', () => {
    it('contains all five codes', () => {
      expect(Object.keys(DISCOUNT_CODES).sort()).toEqual(
        ['FLAT15', 'FLAT5', 'HALF', 'SAVE10', 'SAVE20']
      );
    });

    it('defines percentage codes correctly', () => {
      expect(DISCOUNT_CODES.SAVE10).toEqual({ type: 'percentage', value: 10 });
      expect(DISCOUNT_CODES.SAVE20).toEqual({ type: 'percentage', value: 20 });
      expect(DISCOUNT_CODES.HALF).toEqual({ type: 'percentage', value: 50 });
    });

    it('defines fixed codes correctly', () => {
      expect(DISCOUNT_CODES.FLAT5).toEqual({ type: 'fixed', value: 5 });
      expect(DISCOUNT_CODES.FLAT15).toEqual({ type: 'fixed', value: 15 });
    });
  });
});
