# КАРТЫ МОДУЛЕЙ ОС ДИСПАК

Максимально подробные структурные карты модулей, составленные из текстов `.be` с привязкой к номерам строк. Формат описан в [ФОРМАТ.md](ФОРМАТ.md). Сырые факты (полный перечень меток, ВХОД, ВНЕШ) лежат в `raw_<МОДУЛЬ>.txt`, проверка полноты — `python3 ai/карты/validate.py`.

Карты дополняют [справочники](../СПРАВОЧНИКИ.md): справочник даёт смысл, карта — полную структуру со всеми метками и связями.

## Центральный резидент и ввод

| Модуль | Карта | Исходник | Строк | ВХОД | ВНЕШ |
|---|---|---|---:|---:|---:|
| ДИСП70 | [карта_ДИСП70.md](карта_ДИСП70.md) | disp70.be | 3337 | 82 | 28 |
| ВЗУ | [карта_ВЗУ.md](карта_ВЗУ.md) | vzu.be | 2684 | 17 | 47 |
| ТЕРМ | [карта_ТЕРМ.md](карта_ТЕРМ.md) | term.be | 747 | 3 | 31 |
| МОТТ | [карта_МОТТ.md](карта_МОТТ.md) | mott.be | 2868 | 32 | 41 |

## Управление памятью и задачами

| Модуль | Карта | Исходник | Строк | ВХОД | ВНЕШ |
|---|---|---|---:|---:|---:|
| БОЭК1 | [карта_БОЭК1.md](карта_БОЭК1.md) | boek1.be | 3957 | 13 | 81 |
| ВИСП | [карта_ВИСП.md](карта_ВИСП.md) | visp.be | 404 | 1 | 7 |
| КАЧКА | [карта_КАЧКА.md](карта_КАЧКА.md) | kachka.be | 64 | 6 | 1 |
| КИТ | [карта_КИТ.md](карта_КИТ.md) | kit.be | 169 | 14 | 25 |
| УКАЧКА | [карта_УКАЧКА.md](карта_УКАЧКА.md) | ukachka.be | 594 | 1 | 21 |

## Внешние устройства и связь

| Модуль | Карта | Исходник | Строк | ВХОД | ВНЕШ |
|---|---|---|---:|---:|---:|
| ДИСКИ | [карта_ДИСКИ.md](карта_ДИСКИ.md) | diski.be | 2527 | 20 | 31 |
| ДМЛМБ | [карта_ДМЛМБ.md](карта_ДМЛМБ.md) | dmlmb.be | 2884 | 12 | 42 |
| СВЯЗЬ7 | [карта_СВЯЗЬ7.md](карта_СВЯЗЬ7.md) | svyaz7.be | 1767 | 2 | 18 |
| ОСА | [карта_ОСА.md](карта_ОСА.md) | osa.be | 3152 | 2 | 22 |
| ЕСМЛ | [карта_ЕСМЛ.md](карта_ЕСМЛ.md) | esml.be | 2302 | 5 | 26 |

## Нерезидентные системы

| Модуль | Карта | Исходник | Строк | ВХОД | ВНЕШ |
|---|---|---|---:|---:|---:|
| НОМБОБ | [карта_НОМБОБ.md](карта_НОМБОБ.md) | nombob.be | 1604 | 14 | 35 |
| СМЕ | [карта_СМЕ.md](карта_СМЕ.md) | sme.be | 643 | 1 | 13 |
| СМЕНА1 | [карта_СМЕНА1.md](карта_СМЕНА1.md) | smena1.be | 662 | 2 | 19 |
| СМЕНА2 | [карта_СМЕНА2.md](карта_СМЕНА2.md) | smena2.be | 297 | 1 | 4 |
| СМЕНА3 | [карта_СМЕНА3.md](карта_СМЕНА3.md) | smena3.be | 593 | 1 | 15 |
| ХЛАМ | [карта_ХЛАМ.md](карта_ХЛАМ.md) | khlam.be | 2725 | 12 | 86 |

## Приказы и задачи

| Модуль | Карта | Исходник | Строк | ВХОД | ВНЕШ |
|---|---|---|---:|---:|---:|
| БОНБОТ | [карта_БОНБОТ.md](карта_БОНБОТ.md) | bonbot.be | 2064 | 2 | 23 |
| ПУСКАЧ | [карта_ПУСКАЧ.md](карта_ПУСКАЧ.md) | puskach.be | 742 | 10 | 23 |
| СКОР1 | [карта_СКОР1.md](карта_СКОР1.md) | skor1.be | 712 | 2 | 19 |
| СКОР2 | [карта_СКОР2.md](карта_СКОР2.md) | skor2.be | 789 | 3 | 24 |
| ПРОЦЕС | [карта_ПРОЦЕС.md](карта_ПРОЦЕС.md) | proces.be | 2666 | 3 | 25 |
| ПРОРОК | [карта_ПРОРОК.md](карта_ПРОРОК.md) | prorok.be | 730 | 0 | 21 |
| КАНАЛ | [карта_КАНАЛ.md](карта_КАНАЛ.md) | kanal.be | 2612 | 4 | 40 |
| РЕСУРС | [карта_РЕСУРС.md](карта_РЕСУРС.md) | resurs.be | 2343 | 3 | 31 |

## Генератор и вспомогательные

| Модуль | Карта | Исходник | Строк | ВХОД | ВНЕШ |
|---|---|---|---:|---:|---:|
| ГЕНС | [карта_ГЕНС.md](карта_ГЕНС.md) | gens.be | 2347 | 11 | 16 |
| ГЕНС1 | [карта_ГЕНС1.md](карта_ГЕНС1.md) | gens1.be | 2144 | 3 | 42 |
| ГЕНС2 | [карта_ГЕНС2.md](карта_ГЕНС2.md) | gens2.be | 1113 | 0 | 17 |
| КОНФУС | [карта_КОНФУС.md](карта_КОНФУС.md) | konfus.be | 1084 | 10 | 23 |
| АВМД | [карта_АВМД.md](карта_АВМД.md) | avmd.be | 2142 | 3 | 23 |
| АВМЛ | [карта_АВМЛ.md](карта_АВМЛ.md) | avml.be | 1115 | 0 | 23 |
| ТРУБКА | [карта_ТРУБКА.md](карта_ТРУБКА.md) | trubka.be | 841 | 3 | 17 |
| ДУДКА | [карта_ДУДКА.md](карта_ДУДКА.md) | dudka.be | 393 | 1 | 3 |
| ЭКВВОД | [карта_ЭКВВОД.md](карта_ЭКВВОД.md) | ekvvod.be | 1896 | 6 | 34 |

## Остальные модули проекта

| Модуль | Карта | Исходник | Строк | ВХОД | ВНЕШ |
|---|---|---|---:|---:|---:|
| APUNKT | [карта_APUNKT.md](карта_APUNKT.md) | apunkt.be | 325 | 0 | 5 |
| ARFA | [карта_ARFA.md](карта_ARFA.md) | arfa.be | 3629 | 19 | 49 |
| ARKHIN | [карта_ARKHIN.md](карта_ARKHIN.md) | arkhin.be | 1845 | 2 | 41 |
| AVRASP | [карта_AVRASP.md](карта_AVRASP.md) | avrasp.be | 1585 | 2 | 24 |
| BAC | [карта_BAC.md](карта_BAC.md) | bac.be | 2015 | 0 | 8 |
| BENSON | [карта_BENSON.md](карта_BENSON.md) | benson.be | 367 | 1 | 6 |
| BOP | [карта_BOP.md](карта_BOP.md) | bop.be | 465 | 1 | 23 |
| BOP1 | [карта_BOP1.md](карта_BOP1.md) | bop1.be | 541 | 1 | 24 |
| BOP2 | [карта_BOP2.md](карта_BOP2.md) | bop2.be | 259 | 0 | 4 |
| BUDGET | [карта_BUDGET.md](карта_BUDGET.md) | budget.be | 3355 | 0 | 0 |
| CIRKUL | [карта_CIRKUL.md](карта_CIRKUL.md) | cirkul.be | 649 | 0 | 22 |
| CLOCK | [карта_CLOCK.md](карта_CLOCK.md) | clock.be | 250 | 0 | 5 |
| CONSUL | [карта_CONSUL.md](карта_CONSUL.md) | consul.be | 414 | 1 | 12 |
| DNEPR | [карта_DNEPR.md](карта_DNEPR.md) | dnepr.be | 1920 | 1 | 36 |
| E60 | [карта_E60.md](карта_E60.md) | e60.be | 443 | 0 | 12 |
| E60D | [карта_E60D.md](карта_E60D.md) | e60d.be | 191 | 1 | 1 |
| E64 | [карта_E64.md](карта_E64.md) | e64.be | 1512 | 2 | 13 |
| E71TK | [карта_E71TK.md](карта_E71TK.md) | e71tk.be | 709 | 0 | 15 |
| EK2 | [карта_EK2.md](карта_EK2.md) | ek2.be | 551 | 3 | 26 |
| EK3 | [карта_EK3.md](карта_EK3.md) | ek3.be | 541 | 2 | 30 |
| EK4 | [карта_EK4.md](карта_EK4.md) | ek4.be | 460 | 1 | 17 |
| EK5 | [карта_EK5.md](карта_EK5.md) | ek5.be | 535 | 1 | 18 |
| EK6 | [карта_EK6.md](карта_EK6.md) | ek6.be | 524 | 5 | 23 |
| EK7 | [карта_EK7.md](карта_EK7.md) | ek7.be | 325 | 2 | 13 |
| EKGDR | [карта_EKGDR.md](карта_EKGDR.md) | ekgdr.be | 1897 | 2 | 23 |
| EKO | [карта_EKO.md](карта_EKO.md) | eko.be | 366 | 1 | 12 |
| EKST | [карта_EKST.md](карта_EKST.md) | ekst.be | 475 | 2 | 21 |
| ESPI80 | [карта_ESPI80.md](карта_ESPI80.md) | espi80.be | 414 | 0 | 5 |
| ESPL | [карта_ESPL.md](карта_ESPL.md) | espl.be | 320 | 0 | 5 |
| ESUVVK | [карта_ESUVVK.md](карта_ESUVVK.md) | esuvvk.be | 115 | 1 | 5 |
| FMT | [карта_FMT.md](карта_FMT.md) | fmt.be | 1214 | 0 | 0 |
| GEN | [карта_GEN.md](карта_GEN.md) | gen.be | 2297 | 1 | 15 |
| GIDRA | [карта_GIDRA.md](карта_GIDRA.md) | gidra.be | 1629 | 3 | 49 |
| GNUS | [карта_GNUS.md](карта_GNUS.md) | gnus.be | 282 | 0 | 39 |
| GP1 | [карта_GP1.md](карта_GP1.md) | gp1.be | 559 | 2 | 0 |
| GP2 | [карта_GP2.md](карта_GP2.md) | gp2.be | 107 | 0 | 7 |
| GP3 | [карта_GP3.md](карта_GP3.md) | gp3.be | 164 | 0 | 3 |
| GP4 | [карта_GP4.md](карта_GP4.md) | gp4.be | 573 | 0 | 0 |
| GRUPPA | [карта_GRUPPA.md](карта_GRUPPA.md) | gruppa.be | 307 | 2 | 7 |
| INSERP | [карта_INSERP.md](карта_INSERP.md) | inserp.be | 1270 | 0 | 0 |
| IO | [карта_IO.md](карта_IO.md) | io.be | 269 | 1 | 1 |
| JANUS | [карта_JANUS.md](карта_JANUS.md) | janus.be | 1702 | 0 | 10 |
| KCH | [карта_KCH.md](карта_KCH.md) | kch.be | 181 | 0 | 5 |
| KOKA | [карта_KOKA.md](карта_KOKA.md) | koka.be | 620 | 0 | 0 |
| KOMAR | [карта_KOMAR.md](карта_KOMAR.md) | komar.be | 1087 | 55 | 6 |
| KONVOY | [карта_KONVOY.md](карта_KONVOY.md) | konvoy.be | 465 | 2 | 7 |
| KZ | [карта_KZ.md](карта_KZ.md) | kz.be | 583 | 3 | 17 |
| KZ1 | [карта_KZ1.md](карта_KZ1.md) | kz1.be | 1939 | 2 | 40 |
| MACROS | [карта_MACROS.md](карта_MACROS.md) | macros.be | 234 | 4 | 4 |
| METKI | [карта_METKI.md](карта_METKI.md) | metki.be | 1451 | 1 | 0 |
| NAKOPL | [карта_NAKOPL.md](карта_NAKOPL.md) | nakopl.be | 1301 | 1 | 27 |
| NAKZAD | [карта_NAKZAD.md](карта_NAKZAD.md) | nakzad.be | 1594 | 1 | 28 |
| NEREZA | [карта_NEREZA.md](карта_NEREZA.md) | nereza.be | 1727 | 3 | 45 |
| NEROT | [карта_NEROT.md](карта_NEROT.md) | nerot.be | 469 | 1 | 10 |
| NRKOD | [карта_NRKOD.md](карта_NRKOD.md) | nrkod.be | 1201 | 1 | 6 |
| NROT | [карта_NROT.md](карта_NROT.md) | nrot.be | 327 | 2 | 13 |
| OBRAZ | [карта_OBRAZ.md](карта_OBRAZ.md) | obraz.be | 1748 | 1 | 42 |
| OSANER | [карта_OSANER.md](карта_OSANER.md) | osaner.be | 916 | 1 | 10 |
| OVD | [карта_OVD.md](карта_OVD.md) | ovd.be | 1769 | 4 | 12 |
| PCHKZ | [карта_PCHKZ.md](карта_PCHKZ.md) | pchkz.be | 1431 | 2 | 21 |
| PECHAT | [карта_PECHAT.md](карта_PECHAT.md) | pechat.be | 1482 | 1 | 12 |
| PEREKH | [карта_PEREKH.md](карта_PEREKH.md) | perekh.be | 1829 | 1 | 11 |
| PGS | [карта_PGS.md](карта_PGS.md) | pgs.be | 1616 | 1 | 5 |
| PIBESM | [карта_PIBESM.md](карта_PIBESM.md) | pibesm.be | 418 | 1 | 7 |
| PK | [карта_PK.md](карта_PK.md) | pk.be | 563 | 0 | 0 |
| PLAN | [карта_PLAN.md](карта_PLAN.md) | plan.be | 475 | 1 | 23 |
| PLAN2 | [карта_PLAN2.md](карта_PLAN2.md) | plan2.be | 1164 | 1 | 31 |
| PLBESM | [карта_PLBESM.md](карта_PLBESM.md) | plbesm.be | 330 | 0 | 4 |
| PRIK1 | [карта_PRIK1.md](карта_PRIK1.md) | prik1.be | 561 | 0 | 22 |
| PRIK2 | [карта_PRIK2.md](карта_PRIK2.md) | prik2.be | 504 | 0 | 17 |
| PRIK3 | [карта_PRIK3.md](карта_PRIK3.md) | prik3.be | 354 | 0 | 10 |
| PRIK4 | [карта_PRIK4.md](карта_PRIK4.md) | prik4.be | 668 | 0 | 29 |
| PRIK5 | [карта_PRIK5.md](карта_PRIK5.md) | prik5.be | 592 | 0 | 19 |
| PRIK6 | [карта_PRIK6.md](карта_PRIK6.md) | prik6.be | 583 | 0 | 17 |
| PRIK7 | [карта_PRIK7.md](карта_PRIK7.md) | prik7.be | 523 | 0 | 13 |
| PRIK8 | [карта_PRIK8.md](карта_PRIK8.md) | prik8.be | 158 | 0 | 6 |
| PRISKV | [карта_PRISKV.md](карта_PRISKV.md) | priskv.be | 584 | 0 | 13 |
| PROARX | [карта_PROARX.md](карта_PROARX.md) | proarx.be | 177 | 0 | 0 |
| RA | [карта_RA.md](карта_RA.md) | ra.be | 2399 | 4 | 58 |
| REZARKH | [карта_REZARKH.md](карта_REZARKH.md) | rezarkh.be | 643 | 3 | 19 |
| ROBOT | [карта_ROBOT.md](карта_ROBOT.md) | robot.be | 1725 | 2 | 17 |
| RPIPL | [карта_RPIPL.md](карта_RPIPL.md) | rpipl.be | 368 | 1 | 9 |
| RVS | [карта_RVS.md](карта_RVS.md) | rvs.be | 36 | 0 | 0 |
| SBOR80 | [карта_SBOR80.md](карта_SBOR80.md) | sbor80.be | 1162 | 22 | 3 |
| SERP | [карта_SERP.md](карта_SERP.md) | serp.be | 4329 | 27 | 7 |
| SERP2 | [карта_SERP2.md](карта_SERP2.md) | serp2.be | 2167 | 0 | 0 |
| SERP3 | [карта_SERP3.md](карта_SERP3.md) | serp3.be | 1784 | 1 | 14 |
| SERP4 | [карта_SERP4.md](карта_SERP4.md) | serp4.be | 2826 | 4 | 16 |
| SERP5 | [карта_SERP5.md](карта_SERP5.md) | serp5.be | 1233 | 1 | 8 |
| SIPROG | [карта_SIPROG.md](карта_SIPROG.md) | siprog.be | 1539 | 16 | 2 |
| SLOJKA | [карта_SLOJKA.md](карта_SLOJKA.md) | slojka.be | 1948 | 3 | 0 |
| SOSTAV | [карта_SOSTAV.md](карта_SOSTAV.md) | sostav.be | 93 | 24 | 0 |
| SPE66 | [карта_SPE66.md](карта_SPE66.md) | spe66.be | 486 | 3 | 15 |
| SPOE67 | [карта_SPOE67.md](карта_SPOE67.md) | spoe67.be | 216 | 1 | 7 |
| STAT1S | [карта_STAT1S.md](карта_STAT1S.md) | stat1s.be | 489 | 1 | 15 |
| STAT2S | [карта_STAT2S.md](карта_STAT2S.md) | stat2s.be | 436 | 1 | 15 |
| SVYAZ | [карта_SVYAZ.md](карта_SVYAZ.md) | svyaz.be | 504 | 0 | 8 |
| SVYAZ7_BAK | [карта_SVYAZ7_BAK.md](карта_SVYAZ7_BAK.md) | svyaz7_bak.be | 1755 | 2 | 18 |
| S_TEST | [карта_S_TEST.md](карта_S_TEST.md) | s_test.be | 3969 | 4 | 16 |
| TERMAS | [карта_TERMAS.md](карта_TERMAS.md) | termas.be | 1776 | 0 | 8 |
| TRAKH | [карта_TRAKH.md](карта_TRAKH.md) | trakh.be | 1015 | 0 | 13 |
| TUPR | [карта_TUPR.md](карта_TUPR.md) | tupr.be | 124 | 3 | 2 |
| UPRYACH | [карта_UPRYACH.md](карта_UPRYACH.md) | upryach.be | 466 | 4 | 20 |
| USTSNYA | [карта_USTSNYA.md](карта_USTSNYA.md) | ustsnya.be | 176 | 0 | 0 |
| V1K | [карта_V1K.md](карта_V1K.md) | v1k.be | 1188 | 14 | 28 |
| V3V4 | [карта_V3V4.md](карта_V3V4.md) | v3v4.be | 2039 | 6 | 34 |
| V6V7 | [карта_V6V7.md](карта_V6V7.md) | v6v7.be | 2047 | 3 | 24 |
| VEKTOR | [карта_VEKTOR.md](карта_VEKTOR.md) | vektor.be | 234 | 0 | 0 |
| VYDACH1 | [карта_VYDACH1.md](карта_VYDACH1.md) | vydach1.be | 2570 | 1 | 27 |
| VYDINS | [карта_VYDINS.md](карта_VYDINS.md) | vydins.be | 2979 | 0 | 0 |
| VYZOVD | [карта_VYZOVD.md](карта_VYZOVD.md) | vyzovd.be | 658 | 0 | 0 |
| ZHURNAL | [карта_ZHURNAL.md](карта_ZHURNAL.md) | zhurnal.be | 2148 | 0 | 0 |
| ПРИКАЗ | [карта_ПРИКАЗ.md](карта_ПРИКАЗ.md) | prikaz.be | 1683 | 15 | 34 |
| РУКАВ1 | [карта_РУКАВ1.md](карта_РУКАВ1.md) | rukav1.be | 764 | 0 | 0 |
| РУКАВ2 | [карта_РУКАВ2.md](карта_РУКАВ2.md) | rukav2.be | 1348 | 0 | 0 |
| РУКАВА | [карта_РУКАВА.md](карта_РУКАВА.md) | rukava.be | 3316 | 0 | 0 |
| РУКДКС | [карта_РУКДКС.md](карта_РУКДКС.md) | rukdks.be | 744 | 0 | 0 |
| УЧЕТ | [карта_УЧЕТ.md](карта_УЧЕТ.md) | uchet.be | 216 | 0 | 0 |

Исходники `.be` не изменялись. Карты составлены по тексту модулей.
