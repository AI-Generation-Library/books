function counter() { let n = 0; return () => ++n; }
const next = counter();
console.log(next(), next());
const input = [{ name: 'A', size: 2 }, { name: 'B', size: 3 }];
console.log(input.filter(x => x.size > 2).map(({ name }) => name));
try { JSON.parse('{'); } catch (error) { console.log(error.name); }
