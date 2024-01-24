import threading
import time

import dearpygui.dearpygui as im
from .linktypes import LinkType


def find_node(node_list, node_tag=None):
    if node_tag:
        for i in node_list.copy():
            if i.tag == node_tag:
                return i
    return None


def remove_link(link_list, link_id=None, any_node=None):
        if link_id:
            for i in link_list.copy():
                if i.link_id == link_id:
                    link_list.remove(i)
        elif any_node:
            for i in link_list.copy():
                if i.a_parent == any_node or i.b_parent == any_node:
                    link_list.remove(i)


class Link:
    def __init__(self, a, b, link_id, node_list):
        self.a = a
        self.b = b

        self.a_parent = im.get_item_parent(self.a)
        self.b_parent = im.get_item_parent(self.b)

        self.a_parent_node = find_node(node_list, node_tag=self.a_parent)
        self.b_parent_node = find_node(node_list, node_tag=self.b_parent)

        self.link_id = link_id


def find_link(link_list, a=None, b=None, a_parent=None, b_parent=None):
    res = []
    if a_parent:
        for i in link_list.copy():
            if i.a_parent == a_parent:
                res.append(i)
    elif b_parent:
        for i in link_list.copy():
            if i.b_parent == b_parent:
                res.append(i)
    elif a:
        for i in link_list.copy():
            if i.a == a:
                res.append(i)
    elif b:
        for i in link_list.copy():
            if i.b == b:
                res.append(i)
    return res


class Node:
    def __init__(self, category, label, parent, node_list, link_list):
        self.__category = category
        self.__label = label
        self.__parent = parent
        self.__out_action_item = None
        self.__attributes = []

        self.__node_list = node_list
        self.__link_list = link_list

        self.tag = im.generate_uuid()

        with im.node(label=self.__label, parent=parent, tag=self.tag) if self.__parent else im.node(label=self.__label,
                                                                                               tag=self.tag) as node:
            im.set_item_pos(node, im.get_mouse_pos(local=False))

    def run_next_node(self):
        if self.__out_action_item:
            links = find_link(self.__link_list, a=self.__out_action_item)
            for link in links:
                to_node = link.b_parent_node
                to_node.eval()

    def input_action_attribute(self):
        with im.node_attribute(attribute_type=im.mvNode_Attr_Input, shape=im.mvNode_PinShape_TriangleFilled,
                               filter_key=LinkType.ACTION, parent=self.tag):
            im.add_text("IN ACTION")

    def output_action_attribute(self):
        with im.node_attribute(attribute_type=im.mvNode_Attr_Output, shape=im.mvNode_PinShape_TriangleFilled,
                               filter_key=LinkType.ACTION, parent=self.tag) as attr:
            im.add_text("OUT ACTION")
            self.__out_action_item = attr


class StartNode(Node):
    LABEL_NAME = "Start Node"
    CATEGORY_NAME = "System"

    def __init__(self, node_list: [], link_list: [], parent=None):
        super().__init__(self.CATEGORY_NAME, self.LABEL_NAME, parent, node_list, link_list)
        self.create()
        node_list.append(self)

    def create(self):
        self.output_action_attribute()

    def eval(self):
        self.run_next_node()


class SleepNode(Node):
    LABEL_NAME = "Sleep Node"
    CATEGORY_NAME = "System"

    def __init__(self, node_list: [], link_list: [], parent=None):
        super().__init__(self.CATEGORY_NAME, self.LABEL_NAME, parent, node_list, link_list)
        self.create()
        node_list.append(self)

    def create(self):
        self.input_action_attribute()

        with im.node_attribute(attribute_type=im.mvNode_Attr_Input, filter_key=LinkType.NUM, parent=self.tag) as attr:
            im.add_text("Time")

        self.output_action_attribute()

    def eval(self):
        def f():
            time.sleep(3.0)
            self.run_next_node()

        t = threading.Thread(target=f)
        t.start()


class PrintNode(Node):
    LABEL_NAME = "Print Node"
    CATEGORY_NAME = "System"

    def __init__(self, node_list: [], link_list: [], parent=None):
        super().__init__(self.CATEGORY_NAME, self.LABEL_NAME, parent, node_list, link_list)
        self.create()
        node_list.append(self)

    def create(self):
        self.input_action_attribute()

        with im.node_attribute(attribute_type=im.mvNode_Attr_Input, filter_key=LinkType.NUM, parent=self.tag) as attr:
            im.add_input_text(label="Text", width=150)

        self.output_action_attribute()

    def eval(self):
        print('test')
        self.run_next_node()


def _get_popup_window(node_classes, start_callback, create_node_callback):

    tag = im.generate_uuid()
    with im.window(tag=tag, no_move=True, no_close=True, no_resize=True, no_collapse=True,
                   label="Tools", show=False):

        catalog = {}
        for cls in node_classes:
            node_name = cls.LABEL_NAME
            node_category = cls.CATEGORY_NAME
            if node_category not in catalog:
                catalog[node_category] = []
                catalog[node_category].append(node_name)
            else:
                catalog[node_category].append(node_name)

        for category in catalog:
            with im.menu(label=category):
                for node in catalog[category]:
                    im.add_menu_item(label=node, callback=create_node_callback)

        im.add_button(label="Start", callback=start_callback)
    return tag


def remove_node(node_list, node=None):
    if node:
        for i in node_list.copy():
            if i.tag == node:
                node_list.remove(i)


class __NodeEditor:
    def __init__(self):
        self.node_list = []
        self.link_list = []
        self.node_classes = _get_subclasses(Node)
        self.node_editor_tag = im.generate_uuid()

        with im.handler_registry():
            im.add_key_release_handler(key=im.mvKey_Delete, callback=self.delete_callback)
            im.add_mouse_click_handler(button=1, callback=self.left_click_callback)
            im.add_mouse_click_handler(button=0, callback=self.right_click_callback)

        self.popup_window_tag = _get_popup_window(self.node_classes, self.start_callback, self.create_node_callback)

        with im.node_editor(callback=self.link_callback, delink_callback=self.delink_callback, tag=self.node_editor_tag):
            StartNode(node_list=self.node_list, link_list=self.link_list)

    def start_callback(self):
        # print("-----------------------\n[LINKS]")
        # for l in self.link_list:
        #     print(f"- LINK(parent: a = {l.a_parent}, b = {l.b_parent}; link_id: {l.link_id})")
        # print("\n[NODES]")
        # for n in self.node_list:
        #     print(f"- NODE(tag: {n.tag})")

        for node in self.node_list:
            if node.__class__ == StartNode:
                node.eval()

    def create_node_callback(self, sender):
        found_classes = [cls for cls in self.node_classes if cls.LABEL_NAME == im.get_item_label(sender)]
        if found_classes:
            found_classes[0](node_list=self.node_list, link_list=self.link_list, parent=self.node_editor_tag)

    def delete_callback(self):
        for node in im.get_selected_nodes(self.node_editor_tag):
            remove_link(self.link_list, any_node=node)
            remove_node(self.node_list, node=node)

            try:
                im.delete_item(node)
            except:
                pass

    def link_callback(self, sender, app_data):
        filter_fist = im.get_item_filter_key(app_data[0])
        filter_second = im.get_item_filter_key(app_data[1])

        if filter_fist == filter_second or (filter_second == LinkType.ANY and filter_fist != LinkType.ACTION):
            link_id = im.add_node_link(app_data[0], app_data[1], parent=sender)
            self.link_list.append(Link(app_data[0], app_data[1], link_id, self.node_list))

    def delink_callback(self, sender, app_data):
        im.delete_item(app_data)
        remove_link(self.link_list, link_id=app_data)

    def left_click_callback(self):
        im.focus_item(self.popup_window_tag)
        im.show_item(self.popup_window_tag)
        im.set_item_pos(self.popup_window_tag, im.get_mouse_pos(local=False))

    def right_click_callback(self):
        if im.is_item_hovered(self.node_editor_tag):
            im.hide_item(self.popup_window_tag)


def code_node_editor():
    return __NodeEditor()


def _get_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__() for g in _get_subclasses(s)]