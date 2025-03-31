# mdxrp


`mdxrp` is a set of markdown extensions and a preprocessor for converting the
mdx into valid markdown.  So far these extensions only add the ability
to include labels and references. 

## Installation

```bash
pip install git@github.com:dosirrah/mdx.git
```

Alternatively, you can clone the repository:

    git clone https://github.com/dosirrah/mdx.git
    cd mdx
    pip install .

## Markdown for Labels and References

Standard Markdown lacks built-in support for **automatic numbering and
referencing**, which can make it difficult to maintain consistency in
structured documents such as exams, research papers, and reports. This
system introduces `@` for **labels** and `#` for **references**,
offering a **lightweight, intuitive** solution that integrates
seamlessly into Markdown.


## Example Usage

### Markdown with Labels and References (`.mdx` file)

```
  ## Section @intro: Introduction

  Refer to section #intro for the introduction.

  [...]

  ## Section @analysis: Analysis

  When we refer to the analysis section we would write section #analysis.
```

```
  ## Section 1: Introduction
  
  Refer to section 1 for the introduction.

  [...]

  ## Section 2: Analysis

  When we refer to the analysis section we would write section 2.
```

Above example serves as the most basic case.  We have a single
enumeration that starts with 1 and increments each time we encounter a
"@foo" where "foo" can be replaced with any human-meaningful label
terminated with a space or other non-alphanumeric character.  Any
instance of "#foo" is treated as a reference to "@foo" and uses the
number that was assigned to "@foo".

### **Why `@` for Labels?**

- Inspired by **LaTeX `\label{}`**, which assigns reference points to
  sections, equations, figures, etc.

- Provides a **concise and unobtrusive** way to define labels in
  Markdown.

### **Why `#` for References?**

- Inspired by **hashtags in social media** (e.g., Twitter, X) and
  **HTML anchors**.

- `#` is a natural choice for **inline references**, allowing authors
  to refer to previously defined labels.

### Key Advantages

* **Minimalist** – Avoids complex syntax, making it easy to read and
    write.

* **Non-Disruptive** – `#` is already used for headings in Markdown,
    but only at the start of a line, ensuring no conflict.

* **Scalable** – Supports multiple enumerations (`@prob:foo`,
    `@fig:diagram1`) while allowing a default global numbering
    (`@intro` → `#intro`).

## Named Enumerations and the Global Enumeration

In this Markdown extension, we introduce two types of enumerations to
support structured numbering and referencing: *named enumerations* and
the *global enumeration*.

A *named enumeration* allows authors to maintain separate numbering
sequences for different types of content. This is useful when a
document contains multiple independent categories of numbered
elements, such as problems, figures, tables, sections, or
equations. For example, an author might label a figure as
`@fig:graph1` and reference it later as `#fig:graph1`, ensuring that
figures are numbered independently from other elements.

The *global enumeration*, on the other hand, provides a default
numbering sequence for cases where a single, dominant type of numbered
reference appears throughout the document. Instead of requiring
authors to specify a category each time, they can simply write
`@label` and refer to it as `#label`. This makes the markup cleaner
and more intuitive, particularly for documents where one type of
content—such as problems in an exam or figures in a research paper—is
the primary focus.

By supporting both named and global enumerations, this system achieves
a balance between flexibility and simplicity. While named enumerations
allow for structured organization across multiple categories, the
global enumeration reduces unnecessary complexity for the common
case. In most structured documents, one type of numbered element tends
to dominate, whether it’s exam problems, numbered research findings,
or legal clauses. The global enumeration eliminates the need to
repeatedly specify a category, streamlining the writing process.

At the same time, authors who require multiple sequences can still do
so by using named enumerations. This ensures that documents remain
easy to write and maintain while still providing the necessary
structure for more complex formatting. By combining the efficiency of
a default global numbering system with the flexibility of independent
enumerations, this extension enhances Markdown’s usability without
sacrificing its lightweight nature.

The first example given in this document used the global enumeration.
It is appropriate for a document that has one dominant enumeration
that spans the entire document.  To define a label in the global
enumeration, simply use `@label`. References to the label use
`#label`, and numbering is assigned automatically.

```markdown
## @intro: Introduction

Refer to section #intro for details.

### Problem @mean

Refer to #mean for instructions.
```


### Named Enumerations

Named enumerations allow separate numbering for different categories,
such as figures, tables, and problems. To define a label within a
named enumeration, use @category:label. References follow the same
format: #category:label.  The author can choose any name in place
of `category`.   For example `s` might refer to the enumeration for
section headings.

```
  ## Section @s:intro
```

The string `@s:intro` is replaced with the number 1.

```
  ## Section 1
```

We later refer to section 1 using `#s:intro`.
