from wtforms import StringField, PasswordField, BooleanField, TextAreaField, FileField,SelectField,IntegerField, SelectField, RadioField
from wtforms.validators import InputRequired, Email, Length
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min = 4, max = 50)])
    password = PasswordField( validators=[InputRequired(), Length(min=8, max = 80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid Email'), Length(max = 50)])
    username = StringField('username', validators=[InputRequired(), Length(min = 4, max = 15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max = 80)])

class StudentLoginForm(FlaskForm):
    nickname = StringField('username', validators=[InputRequired(), Length(min = 1, max = 15)])


class QuestionForm(FlaskForm):
    quiz = SelectField('Quiz', coerce=int)
    image = FileField('Image') 
    question = StringField('Question', validators=[DataRequired(), Length(min=4, max=150)])
    question_type = SelectField('Question Type', choices=[('multiple_choice', 'Multiple Choice'), ('true_false', 'True/False'), ('open_question','Open question')], default='true_false')
    question_truefalse = SelectField('Question True/False', choices=[('True', 'True'), ('False', 'False')])
    answer1 = StringField('Answer 1', validators=[Length(min=1, max=75)])
    answer2 = StringField('Answer 2', validators=[Length(min=1, max=75)])
    answer3 = StringField('Answer 3', validators=[Length(min=1, max=75)])
    answer4 = StringField('Answer 4', validators=[Length(min=1, max=75)])
    correct_answer = BooleanField('Correct')

    
class QuizForm(FlaskForm):
    quizTitle = StringField('Title', validators=[DataRequired()])
    quizDescription = TextAreaField('Description')
    quizDuration = SelectField('Duration', coerce=int, validators=[DataRequired()], choices=[
        (15, '15 seconds'),
        (30, '30 seconds'),
        (45, '45 seconds'),
        (60, '60 seconds'),
        (90, '90 seconds'),
        (120, '120 seconds')
    ])
    is_public = SelectField('Is this quiz public?', choices=[('yes', 'Yes'), ('no', 'No')])


    
class QuizCodeForm(FlaskForm):
    quiz_code = IntegerField('Quiz Code', validators=[DataRequired()], render_kw={"placeholder": "Enter the Game Code"})

