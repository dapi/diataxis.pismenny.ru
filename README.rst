Diátaxis по-русски
==================

Неофициальный русский перевод `Diátaxis <https://diataxis.fr/>`_ — системы
для проектирования и написания технической документации.

Публичная бета-версия: https://diataxis.pismenny.ru/. Машинный черновик
опубликован с сохранением источников и проходит последовательную редакторскую
вычитку; найденные неточности исправляются в gettext-каталоге.

Происхождение и лицензия
------------------------

Оригинал создан `Daniele Procida <https://vurt.org>`_ и развивается в
`evildmp/diataxis-documentation-framework
<https://github.com/evildmp/diataxis-documentation-framework>`_. Этот перевод
является производной работой: текст переведён на русский язык, добавлены
атрибуция, русская навигация, ссылка на pismenny.ru и собственная доставка.

Оригинал и перевод распространяются по лицензии
`Creative Commons Attribution-ShareAlike 4.0 International
<https://creativecommons.org/licenses/by-sa/4.0/>`_. Проект не является
официальной русской версией Diátaxis и не подразумевает одобрения автором.

Устройство
----------

Английские исходники находятся в ``source/`` и синхронизируются с remote
``upstream``. Русский перевод хранится отдельно в
``translation/ru/LC_MESSAGES/*.po``. Корень публичного сайта собирается на
русском, английский оригинал доступен в ``/en/``.

Локальная сборка::

    make install
    make site
    make test

Черновое заполнение новых gettext-строк выполняется Google Translate только
для публичного английского оригинала. Локальный Argos Translate остаётся
доступным как запасной provider. После машинного прохода обязательны сборка,
проверка терминологии и редакторская вычитка::

    uv run --python 3.12 --with-requirements requirements-translation.txt \
      python scripts/fill_ru_catalog.py --force

Deployment
----------

Immutable image публикуется в registry goga-office и разворачивается из
``~/code/brandymint/infra`` через Helmfile::

    make deploy
