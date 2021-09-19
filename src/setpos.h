// This file is a part of "Candle" application.
// Copyright 2021 HJLiaw

#ifndef SETPOS_H
#define SETPOS_H

#include <QDialog>

namespace Ui {
class setPos;
}

class setPos : public QDialog
{
    Q_OBJECT

public:
	double pos;
	int    unit;  // 0=mm hardcoded in frmmain.cpp
	QString axis;
	void updateAxisPos();
    explicit setPos(QWidget *parent = 0);
    ~setPos();

private slots:
    void on_pushButtonKey0_clicked();
    void on_pushButtonKey1_clicked();
    void on_pushButtonKey2_clicked();
    void on_pushButtonKey3_clicked();
    void on_pushButtonKey4_clicked();
    void on_pushButtonKey5_clicked();
    void on_pushButtonKey6_clicked();
    void on_pushButtonKey7_clicked();
    void on_pushButtonKey8_clicked();
    void on_pushButtonKey9_clicked();
    void on_pushButtonKeyDot_clicked();
    void on_pushButtonKeyEnter_clicked();
    void on_pushButtonKeyBack_clicked();
	void on_pushButtonKeySign_clicked();

	void on_pushButtonCancel_clicked();
	void on_pushButtonUnit_clicked();
	void on_pushButtonMode_clicked();

private:
    Ui::setPos *ui;
};

#endif // SETPOS_H
