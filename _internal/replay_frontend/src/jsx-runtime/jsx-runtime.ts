/*
 * Automatic JSX runtime requires:
 * - jsx
 * - jsxs
 * - Fragment
 */

export function jsx(tag: any, props: any) {
    return createElement(tag, props);
}

export function jsxs(tag: any, props: any) {
    return createElement(tag, props);
}

export function Fragment(props: any) {
    const frag = document.createDocumentFragment();
    appendChildren(frag, props?.children);
    return frag;
}

function createElement(
    tag: string | Function,
    props: any
): Node {
    const {children, ...rest} = props ?? {};

    // Component
    if (typeof tag === "function") {
        return tag({...rest, children});
    }

    // Native element
    const el = document.createElement(tag);

    // props
    for (const key in rest) {
        const value = rest[key];

        if (key === "className") {
            el.setAttribute("class", value);
        } else if (key.startsWith("on") && typeof value === "function") {
            el.addEventListener(key.slice(2).toLowerCase(), value);
        } else if (value !== false && value != null) {
            el.setAttribute(key, String(value));
        }
    }

    appendChildren(el, children);

    return el;
}

function appendChildren(parent: Node, children: any) {
    if (children == null || children === false) return;

    const list = Array.isArray(children) ? children : [children];

    for (const child of list) {
        if (child == null || child === false) continue;

        if (typeof child === "string" || typeof child === "number") {
            parent.appendChild(document.createTextNode(String(child)));
        } else if (child instanceof Node) {
            parent.appendChild(child);
        }
    }
}

