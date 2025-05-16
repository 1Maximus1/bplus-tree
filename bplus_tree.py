import bisect

class BPlusTree:
    def __init__(self, order=4):
        self.order = order
        self.min_keys = order // 2
        self.root = LeafNode(order)
        self.MAX_LENGHT = 50
    
    def hash_name(self, name):
        hash_str = "".join(f"{ord(c) - ord('a') + 10:02d}" for c in name.lower())
        name_len = len(name)
        trailing_zero = ["0"]*(self.MAX_LENGHT - len(hash_str))
        hash_str += "".join(trailing_zero)
        hash_str = hash_str + str(name_len)
        
        return int(hash_str)
    
    def insert(self, name, data):
        key = self.hash_name(name)
        leaf = self.find_leaf(key)
        leaf.insert(key, (name, data))
        
        if leaf.is_overloaded():
            self.split_and_insert(leaf)
    
    def search(self, name):
        key = self.hash_name(name)
        leaf = self.find_leaf(key)
        
        for k, value in leaf.items:
            if k == key and value[0] == name:
                return value[1]
        return None
    
    def search_greater_than(self, name):
        key = self.hash_name(name)
        leaf = self.find_leaf(key)
        results = []

        key_len = int(str(key)[-2:])
        for k, (n, data) in leaf.items:
            k_len = int(str(k)[-2:])
            if k_len >= key_len:
                results.append((n, data))

        current = leaf.next_leaf
        while current:
            for k, (n, data) in current.items:
                results.append((n, data))
            current = current.next_leaf

        return results

    def search_less_than(self, name):
        key = self.hash_name(name)
        results = []

        current = self.root
        while not current.is_leaf:
            current = current.children[0]
        
        key_len = int(str(key)[-2:])
        while current:
            for k, (n, data) in current.items:
                k_len = int(str(k)[-2:])
                if k_len <= key_len:
                    results.append((n, data))
            current = current.next_leaf

        return results

    
    def delete(self, name):
        key = self.hash_name(name)
        leaf = self.find_leaf(key)
        deleted = leaf.delete(key, name)
        
        if deleted and leaf.is_underloaded() and len(self.root.keys) > 1:
            self.handle_underflow(leaf)
    
    def find_leaf(self, key):
        node = self.root
        while not node.is_leaf:
            idx = bisect.bisect_right(node.keys, key) - 1
            if idx < 0:
                idx = 0
            node = node.children[idx]
        return node
    
    def split_and_insert(self, node):
        new_node, push_key = node.split()
        
        if node.is_root():
            new_root = InternalNode(self.order)
            new_root.keys = [push_key]
            new_root.children = [node, new_node]
            self.root = new_root
            node.parent = new_root
            new_node.parent = new_root
        else:
            parent = node.parent
            parent.insert(push_key, new_node)
            
            if parent.is_overloaded():
                self.split_and_insert(parent)
    
    def handle_underflow(self, node):
        if node.is_root():
            if len(node.keys) == 0 and len(node.children) == 1:
                self.root = node.children[0]
                self.root.parent = None
            return
        
        parent = node.parent
        idx = parent.children.index(node)
        
        if idx > 0:
            left_sibling = parent.children[idx-1]
            if not left_sibling.is_underloaded():
                self.redistribute(left_sibling, node, parent, idx-1)
                return
        
        if idx < len(parent.children) - 1:
            right_sibling = parent.children[idx+1]
            if not right_sibling.is_underloaded():
                self.redistribute(node, right_sibling, parent, idx)
                return
        
        if idx > 0:
            left_sibling = parent.children[idx-1]
            self.merge_mierda(left_sibling, node, parent, idx-1)
        else:
            right_sibling = parent.children[idx+1]
            self.merge_mierda(node, right_sibling, parent, idx)
        
        if parent.is_underloaded():
            self.handle_underflow(parent)
    
    def redistribute(self, left, right, parent, idx):
        if left.is_leaf:
            if len(left.items) > len(right.items):
                item = left.items.pop()
                bisect.insort(right.items, item)
                parent.keys[idx] = right.items[0][0]
            else:
                item = right.items.pop(0)
                bisect.insort(left.items, item)
                parent.keys[idx] = right.items[0][0]
        else:
            if len(left.keys) > len(right.keys):
                child = left.children.pop()
                key = left.keys.pop()
                right.children.insert(0, child)
                right.keys.insert(0, parent.keys[idx])
                parent.keys[idx] = key
                child.parent = right
            else:
                child = right.children.pop(0)
                key = right.keys.pop(0)
                left.children.append(child)
                left.keys.append(parent.keys[idx])
                parent.keys[idx] = key
                child.parent = left
    
    def merge_mierda(self, left, right, parent, idx):
        if left.is_leaf:
            left.items.extend(right.items)
            left.next_leaf = right.next_leaf
            if right.next_leaf:
                right.next_leaf.prev_leaf = left
        else:
            left.keys.append(parent.keys.pop(idx))
            left.keys.extend(right.keys)
            left.children.extend(right.children)
            for child in right.children:
                child.parent = left
        
        parent.children.pop(idx+1)
        
        if not parent.keys and parent.is_root():
            self.root = left
            left.parent = None
    
    def print_tree(self, node=None, level=0):
        node = node or self.root
        prefix = "    " * level
        if node.is_leaf:
            print(prefix + "Leaf:", [item[0] for item in node.items])
        else:
            print(prefix + "Node:", node.keys)
            for child in node.children:
                self.print_tree(child, level + 1)


class Node:
    def __init__(self, order):
        self.order = order
        self.keys = []
        self.parent = None
    
    @property
    def is_leaf(self):
        raise NotImplementedError
    
    @property
    def is_root(self):
        return self.parent is None
    
    def is_overloaded(self):
        return len(self.keys) > self.order
    
    def is_underloaded(self):
        return len(self.keys) < self.order // 2
    
    def split(self):
        raise NotImplementedError


class InternalNode(Node):
    def __init__(self, order):
        super().__init__(order)
        self.children = []
    
    @property
    def is_leaf(self):
        return False
    
    def insert(self, key, child):
        idx = bisect.bisect_right(self.keys, key)
        self.keys.insert(idx, key)
        self.children.insert(idx+1, child)
        child.parent = self
    
    def split(self):
        mid = len(self.keys) // 2
        push_key = self.keys[mid]
        
        new_node = InternalNode(self.order)
        new_node.keys = self.keys[mid+1:]
        new_node.children = self.children[mid+1:]
        
        self.keys = self.keys[:mid]
        self.children = self.children[:mid+1]
        
        for child in new_node.children:
            child.parent = new_node
        
        return new_node, push_key


class LeafNode(Node):
    def __init__(self, order):
        super().__init__(order)
        self.items = [] 
        self.prev_leaf = None
        self.next_leaf = None
    
    @property
    def is_leaf(self):
        return True
    
    def insert(self, key, value):
        bisect.insort(self.items, (key, value))
    
    def delete(self, key, name):
        for i, (k, (n, _)) in enumerate(self.items):
            if k == key and n == name:
                self.items.pop(i)
                return True
        return False
    
    def split(self):
        mid = len(self.items) // 2
        new_node = LeafNode(self.order)
        new_node.items = self.items[mid:]
        self.items = self.items[:mid]
        
        new_node.next_leaf = self.next_leaf
        if self.next_leaf:
            self.next_leaf.prev_leaf = new_node
        new_node.prev_leaf = self
        self.next_leaf = new_node
        
        return new_node, new_node.items[0][0]

if __name__ == "__main__":
    phone_book = BPlusTree()

    phone_book.insert("Anna", "555-0101")
    phone_book.insert("Boris", "555-0102")
    phone_book.insert("Clara", "555-0103")
    phone_book.insert("Dmytro", "555-0104")
    phone_book.insert("Eva", "555-0105")
    phone_book.insert("Frank", "555-0106")
    phone_book.insert("Galina", "555-0107")
    phone_book.insert("Kate", "555-0107")
    
    print("Телефон Анни:", phone_book.search("Anna"))
    print("Телефон Франка:", phone_book.search("Frank"))
    
    print("\nІмена більші за Galina:")
    for name, phone in phone_book.search_greater_than("Galina"):
        print(f"{name}: {phone}")
    
    print("\nІмена менші за Anna:")
    for name, phone in phone_book.search_less_than("Anna"):
        print(f"{name}: {phone}")
    phone_book.print_tree()
    phone_book.delete("Dmytro")
    print("\nТелефон Dmytro після видалення:", phone_book.search("Dmytro"))