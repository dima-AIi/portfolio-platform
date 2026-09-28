import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CaseText } from "./CaseText";

describe("CaseText", () => {
  it("keeps a single paragraph for plain prose", () => {
    const { container } = render(<CaseText text="Клиенты записывались по телефону." />);
    expect(container.querySelectorAll("p")).toHaveLength(1);
    expect(container.querySelector("ul")).toBeNull();
  });

  it("does not glue plain lines of a prose field into one paragraph", () => {
    // Problem/Solution are prose: a wrapped line stays part of the paragraph.
    const { container } = render(<CaseText text={"Первая строка\nвторая строка"} />);
    expect(container.querySelectorAll("p")).toHaveLength(1);
    expect(container.querySelector("p")?.textContent).toBe(
      "Первая строка вторая строка",
    );
  });

  it("turns a run of marked lines into one list", () => {
    render(<CaseText text={"• первый\n• второй\n• третий"} />);
    expect(screen.getAllByRole("listitem").map((li) => li.textContent)).toEqual([
      "первый",
      "второй",
      "третий",
    ]);
  });

  it("renders unmarked lines as list items in one-item-per-line fields", () => {
    // The editor tells the author every line becomes a bullet, so a plain
    // newline-separated list must render as <ul>, not one joined paragraph.
    render(
      <CaseText
        linesAsList
        text={"Личный кабинет с историей записей\nКаталог услуг с ценами и фильтрами"}
      />,
    );
    expect(screen.getByRole("list").tagName).toBe("UL");
    expect(screen.getAllByRole("listitem").map((li) => li.textContent)).toEqual([
      "Личный кабинет с историей записей",
      "Каталог услуг с ценами и фильтрами",
    ]);
    expect(screen.queryByRole("paragraph")).toBeNull();
  });

  it("does not split one list when a marker is typed on some lines only", () => {
    const { container } = render(
      <CaseText linesAsList text={"• первый\nвторой\nтретий"} />,
    );
    const list = container.querySelector("ul") as HTMLElement;
    expect(container.querySelectorAll("ul")).toHaveLength(1);
    expect(within(list).getAllByRole("listitem")).toHaveLength(3);
  });

  it("keeps blank-line blocks separate", () => {
    render(<CaseText linesAsList text={"один\nдва\n\nтри"} />);
    expect(screen.getAllByRole("list")).toHaveLength(2);
  });

  it("lists the shipped ELORA features field as separate items", () => {
    // The exact production value: real newlines, no "•" markers. It rendered
    // as one squashed paragraph before linesAsList existed.
    render(
      <CaseText
        linesAsList
        text={
          "Личный кабинет с историей записей\n" +
          "Каталог услуг с ценами и фильтрами\n" +
          "Галерея работ с фильтром по категориям\n" +
          "PWA с офлайн-оболочкой и манифестом"
        }
      />,
    );
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(4);
    expect(items[0].textContent).toBe("Личный кабинет с историей записей");
    expect(items[3].textContent).toBe("PWA с офлайн-оболочкой и манифестом");
  });
});
