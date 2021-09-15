// modified from qt-virtual-numpad by Dzoka 2016

#include <QDesktopServices>
#include "setpos.h"
#include "ui_setpos.h"
#include "keyemitter.h"

//#include <QDebug>

//extern
KeyEmitter keyEmitter;

setPos::setPos(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::setPos)
{
    ui->setupUi(this);

	QFont font = ui->pushButtonKey0->font();
	font.setPointSize(32);

	foreach( QAbstractButton *button, ui->centralWidget->findChildren<QPushButton*>(QRegExp("pushButtonKey*"))){
		button->setFont(font);
	}

	// enter and back keys will be enlarged to accomodate text, so set a smaller one
	font.setPointSize(18);
	ui->pushButtonKeyEnter->setFont(font);
	ui->pushButtonKeyBack->setFont(font);
	ui->pushButtonKeySign->setFont(font);	
}

setPos::~setPos(){
    delete ui;
}

void setPos::on_pushButtonKey0_clicked(){  keyEmitter.emitKey(Qt::Key_0); }
void setPos::on_pushButtonKey1_clicked(){  keyEmitter.emitKey(Qt::Key_1); }
void setPos::on_pushButtonKey2_clicked(){  keyEmitter.emitKey(Qt::Key_2); }
void setPos::on_pushButtonKey3_clicked(){  keyEmitter.emitKey(Qt::Key_3); }
void setPos::on_pushButtonKey4_clicked(){  keyEmitter.emitKey(Qt::Key_4); }
void setPos::on_pushButtonKey5_clicked(){  keyEmitter.emitKey(Qt::Key_5); }
void setPos::on_pushButtonKey6_clicked(){  keyEmitter.emitKey(Qt::Key_6); }
void setPos::on_pushButtonKey7_clicked(){  keyEmitter.emitKey(Qt::Key_7); }
void setPos::on_pushButtonKey8_clicked(){  keyEmitter.emitKey(Qt::Key_8); }
void setPos::on_pushButtonKey9_clicked(){  keyEmitter.emitKey(Qt::Key_9); }

void setPos::on_pushButtonKeyDot_clicked(){  keyEmitter.emitKey(Qt::Key_Period);    }
void setPos::on_pushButtonKeyBack_clicked(){ keyEmitter.emitKey(Qt::Key_Backspace); }

void setPos::on_pushButtonKeySign_clicked(){
	sync_rad_dia();
	QString sr = ui->lineEditRadius->text();
	if( sr.at( 0 ) == '-' ){
		ui->lineEditRadius->setText( sr.remove(0,1) );
	}
	else{
		ui->lineEditRadius->setText( "-" + sr );
	}
	sync_rad_dia();
}

void setPos:: sync_rad_dia(){
	if( ui->lineEditRadius->hasFocus() ){
		double r = ui->lineEditRadius->text().toDouble();
		ui->lineEditDiameter->setText( QString::number(2*r) );
		//qInfo() << "rad =" << r;
	}

	if( ui->lineEditDiameter->hasFocus() ){
		double d = ui->lineEditDiameter->text().toDouble();
		ui->lineEditRadius->setText( QString::number(d/2) );
		// qInfo() << "dia =" << d;
	}
}

void setPos::on_pushButtonKeyEnter_clicked(){
	sync_rad_dia();       // sync before emitKey, as Tab key changes focus
	keyEmitter.emitKey(Qt::Key_Tab);

	// return 
}
