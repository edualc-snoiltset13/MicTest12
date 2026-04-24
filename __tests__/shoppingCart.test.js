const { ShoppingCart, DISCOUNT_CODES } = require('../src/shoppingCart');

describe('ShoppingCart', () => {
  let cart;

  beforeEach(() => {
    cart = new ShoppingCart();
  });

  describe('constructor', () => {
    it('initializes with an empty items array', () => {
      expect(cart.items).toEqual([]);
    });

    it('initializes with no discount code', () => {
      expect(cart.discountCode).toBeNull();
    });

    it('initializes as not checked out', () => {
      expect(cart.checkedOut).toBe(false);
    });
  });

  describe('addItem', () => {
    it('adds a single item to the cart', () => {
      cart.addItem({ name: 'Apple', price: 1.5 });
      expect(cart.items).toHaveLength(1);
      expect(cart.items[0]).toEqual({ name: 'Apple', price: 1.5, quantity: 1 });
    });

    it('defaults quantity to 1 when not specified', () => {
      cart.addItem({ name: 'Banana', price: 0.75 });
      expect(cart.items[0].quantity).toBe(1);
    });

    it('adds an item with explicit quantity', () => {
      cart.addItem({ name: 'Orange', price: 2.0, quantity: 3 });
      expect(cart.items[0]).toEqual({ name: 'Orange', price: 2.0, quantity: 3 });
    });

    it('merges quantities when adding the same item twice', () => {
      cart.addItem({ name: 'Apple', price: 1.5 });
      cart.addItem({ name: 'Apple', price: 1.5, quantity: 2 });
      expect(cart.items).toHaveLength(1);
      expect(cart.items[0].quantity).toBe(3);
    });

    it('adds multiple different items', () => {
      cart.addItem({ name: 'Apple', price: 1.5 });
      cart.addItem({ name: 'Banana', price: 0.75 });
      cart.addItem({ name: 'Cherry', price: 3.0 });
      expect(cart.items).toHaveLength(3);
    });

    it('returns the cart instance for chaining', () => {
      const result = cart.addItem({ name: 'Apple', price: 1.5 });
      expect(result).toBe(cart);
    });

    it('supports method chaining for multiple adds', () => {
      cart
        .addItem({ name: 'Apple', price: 1.5 })
        .addItem({ name: 'Banana', price: 0.75 });
      expect(cart.items).toHaveLength(2);
    });

    it('handles items with a price of zero', () => {
      cart.addItem({ name: 'Free Sample', price: 0 });
      expect(cart.items[0].price).toBe(0);
    });

    it('throws when item is null', () => {
      expect(() => cart.addItem(null)).toThrow('Item must be an object');
    });

    it('throws when item is undefined', () => {
      expect(() => cart.addItem(undefined)).toThrow('Item must be an object');
    });

    it('throws when item is a string', () => {
      expect(() => cart.addItem('apple')).toThrow('Item must be an object');
    });

    it('throws when item has no name', () => {
      expect(() => cart.addItem({ price: 1.5 })).toThrow('Item must have a valid name');
    });

    it('throws when item name is empty string', () => {
      expect(() => cart.addItem({ name: '', price: 1.5 })).toThrow('Item must have a valid name');
    });

    it('throws when item name is not a string', () => {
      expect(() => cart.addItem({ name: 123, price: 1.5 })).toThrow('Item must have a valid name');
    });

    it('throws when item has no price', () => {
      expect(() => cart.addItem({ name: 'Apple' })).toThrow('Item must have a non-negative price');
    });

    it('throws when item has negative price', () => {
      expect(() => cart.addItem({ name: 'Apple', price: -1 })).toThrow('Item must have a non-negative price');
    });

    it('throws when price is not a number', () => {
      expect(() => cart.addItem({ name: 'Apple', price: '1.50' })).toThrow('Item must have a non-negative price');
    });

    it('throws when quantity is zero', () => {
      expect(() => cart.addItem({ name: 'Apple', price: 1.5, quantity: 0 })).toThrow('Item quantity must be a positive integer');
    });

    it('throws when quantity is negative', () => {
      expect(() => cart.addItem({ name: 'Apple', price: 1.5, quantity: -1 })).toThrow('Item quantity must be a positive integer');
    });

    it('throws when quantity is a decimal', () => {
      expect(() => cart.addItem({ name: 'Apple', price: 1.5, quantity: 1.5 })).toThrow('Item quantity must be a positive integer');
    });

    it('throws when cart is already checked out', () => {
      cart.addItem({ name: 'Apple', price: 1.5 });
      cart.checkout();
      expect(() => cart.addItem({ name: 'Banana', price: 0.75 })).toThrow('Cannot modify a checked-out cart');
    });
  });

  describe('removeItem', () => {
    beforeEach(() => {
      cart.addItem({ name: 'Apple', price: 1.5 });
      cart.addItem({ name: 'Banana', price: 0.75 });
      cart.addItem({ name: 'Cherry', price: 3.0 });
    });

    it('removes an existing item by name', () => {
      cart.removeItem('Banana');
      expect(cart.items).toHaveLength(2);
      expect(cart.items.find(i => i.name === 'Banana')).toBeUndefined();
    });

    it('preserves other items when one is removed', () => {
      cart.removeItem('Banana');
      expect(cart.items.map(i => i.name)).toEqual(['Apple', 'Cherry']);
    });

    it('returns the cart instance for chaining', () => {
      const result = cart.removeItem('Apple');
      expect(result).toBe(cart);
    });

    it('can remove all items one by one', () => {
      cart.removeItem('Apple');
      cart.removeItem('Banana');
      cart.removeItem('Cherry');
      expect(cart.items).toHaveLength(0);
    });

    it('throws when removing an item not in the cart', () => {
      expect(() => cart.removeItem('Dragonfruit')).toThrow('Item "Dragonfruit" not found in cart');
    });

    it('throws when removing an item that was already removed', () => {
      cart.removeItem('Apple');
      expect(() => cart.removeItem('Apple')).toThrow('Item "Apple" not found in cart');
    });

    it('throws when name is null', () => {
      expect(() => cart.removeItem(null)).toThrow('Item name must be a non-empty string');
    });

    it('throws when name is empty string', () => {
      expect(() => cart.removeItem('')).toThrow('Item name must be a non-empty string');
    });

    it('throws when name is not a string', () => {
      expect(() => cart.removeItem(123)).toThrow('Item name must be a non-empty string');
    });

    it('throws when cart is already checked out', () => {
      cart.checkout();
      expect(() => cart.removeItem('Apple')).toThrow('Cannot modify a checked-out cart');
    });

    it('supports chaining remove with add', () => {
      cart.removeItem('Apple').addItem({ name: 'Mango', price: 2.5 });
      expect(cart.items.map(i => i.name)).toEqual(['Banana', 'Cherry', 'Mango']);
    });
  });

  describe('applyDiscount', () => {
    it('applies a valid percentage discount code', () => {
      cart.applyDiscount('SAVE10');
      expect(cart.discountCode).toEqual({ code: 'SAVE10', type: 'percentage', value: 10 });
    });

    it('applies a valid fixed discount code', () => {
      cart.applyDiscount('FLAT5');
      expect(cart.discountCode).toEqual({ code: 'FLAT5', type: 'fixed', value: 5 });
    });

    it('is case-insensitive', () => {
      cart.applyDiscount('save10');
      expect(cart.discountCode.code).toBe('SAVE10');
    });

    it('handles mixed-case input', () => {
      cart.applyDiscount('Flat15');
      expect(cart.discountCode.code).toBe('FLAT15');
    });

    it('replaces a previously applied discount code', () => {
      cart.applyDiscount('SAVE10');
      cart.applyDiscount('SAVE20');
      expect(cart.discountCode.code).toBe('SAVE20');
    });

    it('returns the cart instance for chaining', () => {
      const result = cart.applyDiscount('SAVE10');
      expect(result).toBe(cart);
    });

    it('throws for an invalid discount code', () => {
      expect(() => cart.applyDiscount('BOGUS')).toThrow('Invalid discount code: "BOGUS"');
    });

    it('throws when code is null', () => {
      expect(() => cart.applyDiscount(null)).toThrow('Discount code must be a non-empty string');
    });

    it('throws when code is empty string', () => {
      expect(() => cart.applyDiscount('')).toThrow('Discount code must be a non-empty string');
    });

    it('throws when code is not a string', () => {
      expect(() => cart.applyDiscount(42)).toThrow('Discount code must be a non-empty string');
    });

    it('throws when cart is already checked out', () => {
      cart.addItem({ name: 'Apple', price: 1.5 });
      cart.checkout();
      expect(() => cart.applyDiscount('SAVE10')).toThrow('Cannot modify a checked-out cart');
    });
  });

  describe('calculateTotal', () => {
    it('returns 0 for an empty cart', () => {
      expect(cart.calculateTotal()).toBe(0);
    });

    it('returns the price of a single item', () => {
      cart.addItem({ name: 'Apple', price: 1.5 });
      expect(cart.calculateTotal()).toBe(1.5);
    });

    it('sums prices of multiple items', () => {
      cart.addItem({ name: 'Apple', price: 1.5 });
      cart.addItem({ name: 'Banana', price: 0.75 });
      expect(cart.calculateTotal()).toBe(2.25);
    });

    it('accounts for item quantities', () => {
      cart.addItem({ name: 'Apple', price: 1.5, quantity: 3 });
      expect(cart.calculateTotal()).toBe(4.5);
    });

    it('applies a 10% discount correctly', () => {
      cart.addItem({ name: 'Shirt', price: 50 });
      cart.applyDiscount('SAVE10');
      expect(cart.calculateTotal()).toBe(45);
    });

    it('applies a 20% discount correctly', () => {
      cart.addItem({ name: 'Shirt', price: 100 });
      cart.applyDiscount('SAVE20');
      expect(cart.calculateTotal()).toBe(80);
    });

    it('applies a 50% discount correctly', () => {
      cart.addItem({ name: 'Shirt', price: 80 });
      cart.applyDiscount('HALF');
      expect(cart.calculateTotal()).toBe(40);
    });

    it('applies a fixed $5 discount correctly', () => {
      cart.addItem({ name: 'Shirt', price: 50 });
      cart.applyDiscount('FLAT5');
      expect(cart.calculateTotal()).toBe(45);
    });

    it('applies a fixed $15 discount correctly', () => {
      cart.addItem({ name: 'Shirt', price: 50 });
      cart.applyDiscount('FLAT15');
      expect(cart.calculateTotal()).toBe(35);
    });

    it('does not let fixed discount reduce total below zero', () => {
      cart.addItem({ name: 'Candy', price: 3 });
      cart.applyDiscount('FLAT5');
      expect(cart.calculateTotal()).toBe(0);
    });

    it('handles percentage discount on multiple items with quantities', () => {
      cart.addItem({ name: 'Apple', price: 2, quantity: 5 });
      cart.addItem({ name: 'Banana', price: 3, quantity: 2 });
      cart.applyDiscount('SAVE10');
      expect(cart.calculateTotal()).toBe(14.4);
    });

    it('rounds to two decimal places', () => {
      cart.addItem({ name: 'Item', price: 10.33 });
      cart.applyDiscount('SAVE10');
      expect(cart.calculateTotal()).toBeCloseTo(9.3, 2);
    });

    it('returns correct total when no discount is applied', () => {
      cart.addItem({ name: 'A', price: 10 });
      cart.addItem({ name: 'B', price: 20 });
      expect(cart.calculateTotal()).toBe(30);
    });
  });

  describe('getSubtotal', () => {
    it('returns 0 for an empty cart', () => {
      expect(cart.getSubtotal()).toBe(0);
    });

    it('returns price * quantity for a single item', () => {
      cart.addItem({ name: 'Apple', price: 2, quantity: 4 });
      expect(cart.getSubtotal()).toBe(8);
    });

    it('sums all items correctly', () => {
      cart.addItem({ name: 'Apple', price: 1.5, quantity: 2 });
      cart.addItem({ name: 'Banana', price: 0.5, quantity: 3 });
      expect(cart.getSubtotal()).toBe(4.5);
    });
  });

  describe('getDiscount', () => {
    it('returns 0 when no discount code is applied', () => {
      cart.addItem({ name: 'Apple', price: 10 });
      expect(cart.getDiscount()).toBe(0);
    });

    it('returns the correct percentage-based discount amount', () => {
      cart.addItem({ name: 'Apple', price: 100 });
      cart.applyDiscount('SAVE20');
      expect(cart.getDiscount()).toBe(20);
    });

    it('returns the correct fixed discount amount', () => {
      cart.addItem({ name: 'Apple', price: 100 });
      cart.applyDiscount('FLAT15');
      expect(cart.getDiscount()).toBe(15);
    });

    it('caps fixed discount at the subtotal', () => {
      cart.addItem({ name: 'Candy', price: 3 });
      cart.applyDiscount('FLAT5');
      expect(cart.getDiscount()).toBe(3);
    });

    it('returns 0 discount on an empty cart even with a code applied', () => {
      cart.applyDiscount('SAVE10');
      expect(cart.getDiscount()).toBe(0);
    });
  });

  describe('getItemCount', () => {
    it('returns 0 for an empty cart', () => {
      expect(cart.getItemCount()).toBe(0);
    });

    it('returns 1 for a single item with default quantity', () => {
      cart.addItem({ name: 'Apple', price: 1.5 });
      expect(cart.getItemCount()).toBe(1);
    });

    it('sums quantities across all items', () => {
      cart.addItem({ name: 'Apple', price: 1.5, quantity: 3 });
      cart.addItem({ name: 'Banana', price: 0.75, quantity: 2 });
      expect(cart.getItemCount()).toBe(5);
    });

    it('reflects merged quantities for duplicate items', () => {
      cart.addItem({ name: 'Apple', price: 1.5 });
      cart.addItem({ name: 'Apple', price: 1.5, quantity: 4 });
      expect(cart.getItemCount()).toBe(5);
    });
  });

  describe('checkout', () => {
    it('returns an order summary object', () => {
      cart.addItem({ name: 'Shirt', price: 25, quantity: 2 });
      const order = cart.checkout();
      expect(order).toEqual({
        items: [{ name: 'Shirt', price: 25, quantity: 2 }],
        subtotal: 50,
        discount: 0,
        total: 50,
        itemCount: 2,
        discountCode: null,
      });
    });

    it('includes discount information in the order summary', () => {
      cart.addItem({ name: 'Shirt', price: 100 });
      cart.applyDiscount('SAVE20');
      const order = cart.checkout();
      expect(order).toEqual({
        items: [{ name: 'Shirt', price: 100, quantity: 1 }],
        subtotal: 100,
        discount: 20,
        total: 80,
        itemCount: 1,
        discountCode: 'SAVE20',
      });
    });

    it('returns a shallow copy of items, not a live reference', () => {
      cart.addItem({ name: 'Shirt', price: 25 });
      const order = cart.checkout();
      order.items[0].name = 'Modified';
      expect(cart.items[0].name).toBe('Shirt');
    });

    it('marks the cart as checked out', () => {
      cart.addItem({ name: 'Shirt', price: 25 });
      cart.checkout();
      expect(cart.checkedOut).toBe(true);
    });

    it('throws when checking out an empty cart', () => {
      expect(() => cart.checkout()).toThrow('Cannot checkout an empty cart');
    });

    it('throws when checking out a second time', () => {
      cart.addItem({ name: 'Shirt', price: 25 });
      cart.checkout();
      expect(() => cart.checkout()).toThrow('Cart has already been checked out');
    });

    it('prevents adding items after checkout', () => {
      cart.addItem({ name: 'Shirt', price: 25 });
      cart.checkout();
      expect(() => cart.addItem({ name: 'Hat', price: 15 })).toThrow('Cannot modify a checked-out cart');
    });

    it('prevents removing items after checkout', () => {
      cart.addItem({ name: 'Shirt', price: 25 });
      cart.checkout();
      expect(() => cart.removeItem('Shirt')).toThrow('Cannot modify a checked-out cart');
    });

    it('prevents applying discounts after checkout', () => {
      cart.addItem({ name: 'Shirt', price: 25 });
      cart.checkout();
      expect(() => cart.applyDiscount('SAVE10')).toThrow('Cannot modify a checked-out cart');
    });

    it('handles a complex multi-item order with a discount', () => {
      cart
        .addItem({ name: 'Laptop', price: 999.99 })
        .addItem({ name: 'Mouse', price: 29.99, quantity: 2 })
        .addItem({ name: 'USB Cable', price: 9.99, quantity: 3 })
        .applyDiscount('SAVE10');

      const order = cart.checkout();

      expect(order.itemCount).toBe(6);
      expect(order.subtotal).toBeCloseTo(1089.94, 2);
      expect(order.discount).toBeCloseTo(108.99, 1);
      expect(order.total).toBeCloseTo(order.subtotal - order.discount, 2);
      expect(order.discountCode).toBe('SAVE10');
      expect(order.items).toHaveLength(3);
    });
  });

  describe('integration workflows', () => {
    it('supports a full add-discount-checkout workflow', () => {
      cart.addItem({ name: 'Book', price: 12.99 });
      cart.addItem({ name: 'Pen', price: 1.99, quantity: 5 });
      cart.applyDiscount('FLAT5');

      expect(cart.getItemCount()).toBe(6);
      expect(cart.getSubtotal()).toBeCloseTo(22.94, 2);

      const order = cart.checkout();
      expect(order.total).toBeCloseTo(17.94, 2);
    });

    it('supports add, remove, then checkout', () => {
      cart.addItem({ name: 'A', price: 10 });
      cart.addItem({ name: 'B', price: 20 });
      cart.addItem({ name: 'C', price: 30 });
      cart.removeItem('B');

      const order = cart.checkout();
      expect(order.items).toHaveLength(2);
      expect(order.total).toBe(40);
    });

    it('supports replacing a discount before checkout', () => {
      cart.addItem({ name: 'Item', price: 100 });
      cart.applyDiscount('SAVE10');
      expect(cart.calculateTotal()).toBe(90);

      cart.applyDiscount('SAVE20');
      expect(cart.calculateTotal()).toBe(80);

      const order = cart.checkout();
      expect(order.total).toBe(80);
      expect(order.discountCode).toBe('SAVE20');
    });

    it('multiple independent cart instances do not share state', () => {
      const cart2 = new ShoppingCart();
      cart.addItem({ name: 'A', price: 10 });
      cart2.addItem({ name: 'B', price: 20 });

      expect(cart.items).toHaveLength(1);
      expect(cart2.items).toHaveLength(1);
      expect(cart.items[0].name).toBe('A');
      expect(cart2.items[0].name).toBe('B');
    });

    it('chains all operations fluently', () => {
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

  describe('DISCOUNT_CODES', () => {
    it('exports all expected discount codes', () => {
      expect(Object.keys(DISCOUNT_CODES)).toEqual(
        expect.arrayContaining(['SAVE10', 'SAVE20', 'FLAT5', 'FLAT15', 'HALF'])
      );
    });

    it('has correct structure for percentage codes', () => {
      expect(DISCOUNT_CODES.SAVE10).toEqual({ type: 'percentage', value: 10 });
      expect(DISCOUNT_CODES.SAVE20).toEqual({ type: 'percentage', value: 20 });
      expect(DISCOUNT_CODES.HALF).toEqual({ type: 'percentage', value: 50 });
    });

    it('has correct structure for fixed codes', () => {
      expect(DISCOUNT_CODES.FLAT5).toEqual({ type: 'fixed', value: 5 });
      expect(DISCOUNT_CODES.FLAT15).toEqual({ type: 'fixed', value: 15 });
    });
  });
});
