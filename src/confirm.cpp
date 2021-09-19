// customized confirm window

#include <QDesktopServices>
#include "confirm.h"
#include "ui_confirm.h"

confirm::confirm(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::confirm)
{
    ui->setupUi(this);

	/*
	QFont font = ui->pushButtonKey0->font();
	font.setPointSize(32);
	qDebug() << font;
	*/
}

confirm::~confirm(){
    delete ui;
}

void confirm::on_pushButtonOK_clicked(){
	this->accept();
}

void confirm::on_pushButtonCancel_clicked(){
	this->reject();
}

