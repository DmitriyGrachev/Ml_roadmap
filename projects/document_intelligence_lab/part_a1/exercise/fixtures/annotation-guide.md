# Аннотации независимого задания

Texts написаны отдельно от teacher inventory; permission/license указаны в
[sources.json](sources.json). Это invented notices, без данных реальной библиотеки.

| Главная функция объявления | Label | Пример accepted |
| --- | --- | --- |
| Выдать, вернуть, продлить документ | borrowing | n01: Borrow up to three books for fourteen days. |
| Время посещения, вход или закрытие | access | n04: The library opens at nine on Mondays. |
| Приглашение на запланированное занятие | event | n07: Join the poetry reading on Friday evening. |

«Return a book and join our workshop» — review, две функции, вне accepted data.
«Important notice» — review, функции нет. Пустая строка — rejected.
Не выводите label из слова library: оно встречается в разных категориях.
Аннотация делается по действию до чтения model prediction; исправление ambiguity
требует новой версии data и заранее определённой оценки.

В [splits.json](splits.json) train содержит по три notices каждого label,
validation — по одному, test — по два. Пары n01/n02, n04/n05 и n07/n08 —
авторские пересказы одного правила/события, поэтому каждая пара имеет общий group_id
и целиком остаётся в train. Test пары n13/n14, n15/n16, n17/n18 относятся к другим
семействам: renewal-policy, accessible-route, history-talk; они целиком в test.
Validation — отдельные map-loan, floor-hours, chess-event.
Один и тот же исходный notice с пересказами нельзя назвать разными families ради split.
Эти короткие synthetic notices не оценивают настоящий поток объявлений.
