# mdx


`mdx` is a set of markdown extensions and a preprocessor for converting the
mdx into valid markdown.  So far these extensions only add the ability
to include labels and references. 


## Markdown for Labels and References

Standard Markdown lacks built-in support for **automatic numbering and referencing**, which can make it difficult to maintain consistency in structured documents such as exams, research papers, and reports. This system introduces `@` for **labels** and `#` for **references**, offering a **lightweight, intuitive** solution that integrates seamlessly into Markdown.

### **Why `@` for Labels?**

- Inspired by **LaTeX `\label{}`**, which assigns reference points to sections, equations, figures, etc.
- Provides a **concise and unobtrusive** way to define labels in Markdown.
- Example: `@fig:diagram1` assigns a label `diagram1` under the `fig` category.

### **Why `#` for References?**

- Inspired by **hashtags in social media** (e.g., Twitter, X) and **HTML anchors**.
- `#` is a natural choice for **inline references**, allowing authors to refer to previously defined labels.
- Example: `#fig:diagram1` refers to the labeled figure.

### **Key Advantages**

* **Minimalist** – Avoids complex syntax, making it easy to read and write.  
* **Non-Disruptive** – `#` is already used for headings in Markdown, but only at the start of a line, ensuring no conflict.  
* **Scalable** – Supports multiple enumerations (`@prob:foo`, `@fig:diagram1`) while allowing a default global numbering (`@intro` → `#intro`).  

## **Example Usage**

### **Markdown with Labels and References (`.mdx` file)**

```
  ## Section @s:intro: Introduction

  Refer to #s:intro for the introduction.

  ### Figure @fig:diagram1: Example Diagram
  See #fig:diagram1 for reference.
  
  | Problem ID  | Description                         |
  |-------------|-------------------------------------|
  | @prob:q1    | True or False: Random variables    |
  | @prob:q2    | Define confidence intervals        |
  
  Refer to #prob:q2 for more details.
```

```
  ## Section 1: Introduction
  
  Refer to **1** for the introduction.

  ### Figure 1: Example Diagram
  See **1** for reference.

  | Problem ID  | Description                         |
  |-------------|-------------------------------------|
  | 1           | True or False: Random variables    |
  | 2           | Define confidence intervals        |

  Refer to **2** for more details.
```


