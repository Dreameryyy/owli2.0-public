from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import Quiz, Question, Choice
from forms import QuestionForm, QuizForm
from extensions import UPLOAD_FOLDER,ALLOWED_EXTENSIONS, db
from datetime import datetime
import os


crud = Blueprint('crud', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Route and method for creating a new Question
@crud.route('/fastNewQuestion', methods=['GET', 'POST'])
@login_required
def fastNewQuestion():
    # Instantiate QuestionForm
    form = QuestionForm()

    # Get quizzes created by current user if not admin, otherwise get all quizzes
    if current_user.admin:
        quizzes = Quiz.query.all()
    else:
        quizzes = Quiz.query.filter_by(user_id=current_user.id).all()

    # If no quizzes exist, redirect to create new quiz page
    if not quizzes:
        flash('Please create a quiz before adding a question', 'error')
        return redirect(url_for('crud.newQuiz'))


    # Set the last modified quiz as the default placeholder in the dropdown menu
    last_modified_quiz = sorted(quizzes, key=lambda x: x.modified_at, reverse=True)[0]
    form.quiz.choices = [(q.id, q.title) for q in quizzes]
    form.quiz.default = last_modified_quiz.id
    form.process()

    if request.method == 'POST':
        try:
            # Get the values submitted by the form
            question = request.form['question']
            question_type = request.form['question_type']
            answer1 = request.form['answer1']
            answer2 = request.form['answer2']
            answer3 = request.form['answer3']
            answer4 = request.form['answer4']
            correct_answer = request.form.getlist('correct_answer')
            quiz_id = request.form['quiz']
            

            # Check if at least one correct answer is selected
            if not correct_answer:
                flash("Please select a correct answer", 'error')
                return redirect(url_for("crud.newQuestion"))

            # Create a new question object and add it to the database
            new_question = Question(text=question, quiz_id=quiz_id, question_type=question_type)

            # Update the quiz's modified_at timestamp
            quiz = Quiz.query.filter_by(id=quiz_id).first()
            quiz.modified_at = datetime.utcnow()

            # Add the new question to the database
            db.session.add(new_question)
            db.session.commit()

            # Transform the list of correct answers into a list of integers
            correct_answerList =[]
            for answer in correct_answer:
                correct_answerList.append(int(answer))

             # Check the question type and create the choices accordingly
            if question_type == 'true_false':
                # For yes/no questions, only two choices are needed
                correct_answer_yesno = request.form['question_truefalse']
                new_choice1 = Choice(question_id=new_question.id, text='True',
                         is_correct=True if correct_answer_yesno == 'True' else False)
                new_choice2 = Choice(question_id=new_question.id, text='False',
                         is_correct=True if correct_answer_yesno == 'False' else False)
                db.session.add(new_choice1)
                db.session.add(new_choice2)
            if question_type == 'multiple_choice':
            # Create a new Choice object for each answer choice and add it to the database

                new_choice1 = Choice(question_id=new_question.id, text=answer1,
                     is_correct=True if 1 in correct_answerList else False)
                new_choice2 = Choice(question_id=new_question.id, text=answer2,
                     is_correct=True if 2 in correct_answerList else False)
                new_choice3 = Choice(question_id=new_question.id, text=answer3,
                     is_correct=True if 3 in correct_answerList else False)
                new_choice4 = Choice(question_id=new_question.id, text=answer4,
                     is_correct=True if 4 in correct_answerList else False)

                db.session.add(new_choice1)
                db.session.add(new_choice2)
                db.session.add(new_choice3)
                db.session.add(new_choice4)
            db.session.commit()

            flash('New question has been added to the quiz', 'success')

            # Redirect to the quiz detail page
            return redirect(url_for('crud.fastNewQuestion', quiz_id=quiz_id))
        except Exception as e:
            # Rollback transaction if there's an error and display error message
            db.session.rollback
            flash('An error occurred while adding the question: ' + str(e), 'error')

    return render_template('fastNewQuestion.html', form=form, quizzes=quizzes, quiz_id =last_modified_quiz.id)



# Route for creating a new quiz
@crud.route('/newQuiz', methods=['GET', 'POST'])
@login_required
def newQuiz():
    # Create a new instance of the QuizForm
    form = QuizForm()
    
    # If the form has been submitted and passed validation checks
    if form.validate_on_submit():
        try:
            # Create a new quiz object using the form data
            new_quiz = Quiz(
                title=form.quizTitle.data,
                description=form.quizDescription.data,
                duration=form.quizDuration.data,
                user_id=current_user.id,
                public=form.is_public.data == 'yes')
            print(form.quizTitle.data)
            
            # Add the new quiz object to the database and commit the transaction
            db.session.add(new_quiz)
            db.session.commit()
            
            # Flash a success message to the user
            flash('New quiz has been created', 'success')
            # Clear the form data
            form.process()

        
        # If an exception occurs during the database transaction
        except Exception as e:
            # Rollback the transaction and flash an error message to the user
            db.session.rollback()
            flash('Sorry, something went wrong: ' + str(e), 'error')
    
    # Render the newQuiz.html template with the QuizForm instance
    return render_template('newQuiz.html', form=form)


#route and method to display all quizes of a User
@crud.route('/quizzes')
@login_required  # enforce authentication
def quizzes():

    # if the current user is an admin, show all quizzes
    if current_user.admin:
        quizzes = Quiz.query.all()
    # otherwise, only show quizzes created by the current user
    else:
        quizzes = Quiz.query.filter_by(user_id=current_user.id).all()

    # render the quizzes.html template with the quizzes data
    return render_template('quizzes.html', quizzes=quizzes)
@crud.route('/public')
@login_required 
def public():

    quizzes = Quiz.query.filter_by(public=True).all()

    return render_template('public.html', quizzes=quizzes)

@crud.route('/newQuestion/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def newQuestion(quiz_id):
    
    # Instantiate a new QuestionForm
    form = QuestionForm()

    # Get quizzes created by current user if not admin, otherwise get all quizzes
    if current_user.admin:
        quizzes = Quiz.query.all()
    else:
        quizzes = Quiz.query.filter_by(user_id=current_user.id).all()

    # If there are no quizzes, redirect to create a quiz first
    if not quizzes:
        flash('Please create a quiz before adding a question', 'error')
        return redirect(url_for('crud.newQuiz'))

    # Set the quiz as the default placeholder in the dropdown menu
    quiz = Quiz.query.get(quiz_id)
    form.quiz.choices = [(q.id, q.title) for q in quizzes]
    form.quiz.default = quiz.id
    form.process()

    if request.method == 'POST':
        try:
            # Get the values submitted by the form
            question = request.form['question']
            question_type = request.form['question_type']
            answer1 = request.form['answer1']
            answer2 = request.form['answer2']
            answer3 = request.form['answer3']
            answer4 = request.form['answer4']
            correct_answer = request.form.getlist('correct_answer')
            quiz_id = request.form['quiz']
            

            # Check if at least one correct answer is selected
            if not correct_answer and question_type is not 'open_question':
                flash("Please select a correct answer", 'error')
                return redirect(url_for("crud.newQuestion"))

            # Create a new question object and add it to the database
            new_question = Question(text=question, quiz_id=quiz_id, question_type=question_type)

            # Update the quiz's modified_at timestamp
            quiz = Quiz.query.filter_by(id=quiz_id).first()
            quiz.modified_at = datetime.utcnow()

            # Add the new question to the database
            db.session.add(new_question)
            db.session.commit()

            # Transform the list of correct answers into a list of integers
            correct_answerList =[]
            for answer in correct_answer:
                correct_answerList.append(int(answer))

             # Check the question type and create the choices accordingly
            if question_type == 'true_false':
                # For yes/no questions, only two choices are needed
                correct_answer_yesno = request.form['question_truefalse']
                new_choice1 = Choice(question_id=new_question.id, text='True',
                         is_correct=True if correct_answer_yesno == 'True' else False)
                new_choice2 = Choice(question_id=new_question.id, text='False',
                         is_correct=True if correct_answer_yesno == 'False' else False)
                db.session.add(new_choice1)
                db.session.add(new_choice2)
            if question_type == 'multiple_choice': 
            # Create a new Choice object for each answer choice and add it to the database

                new_choice1 = Choice(question_id=new_question.id, text=answer1,
                     is_correct=True if 1 in correct_answerList else False)
                new_choice2 = Choice(question_id=new_question.id, text=answer2,
                     is_correct=True if 2 in correct_answerList else False)
                new_choice3 = Choice(question_id=new_question.id, text=answer3,
                     is_correct=True if 3 in correct_answerList else False)
                new_choice4 = Choice(question_id=new_question.id, text=answer4,
                     is_correct=True if 4 in correct_answerList else False)

                db.session.add(new_choice1)
                db.session.add(new_choice2)
                db.session.add(new_choice3)
                db.session.add(new_choice4)
            db.session.commit()

            flash('New question has been added to the quiz', 'success')
            return redirect(url_for('crud.newQuestion', quiz_id=quiz_id))
        except Exception as e:
            # If an exception occurs, rollback the database transaction and show an error message
            db.session.rollback()
            flash('Sorry, something went wrong: ' + str(e), 'error')

    # Render the newQuestion template with the QuestionForm, quizzes, and quiz ID as context variables
    return render_template('newQuestion.html', form=form, quizzes=quizzes, quiz_id=quiz.id)

@crud.route('/question/<int:quiz_id>/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(quiz_id, question_id):
    # Get quiz and question objects
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    question = Question.query.filter_by(id=question_id).first()

    # Initialize question form
    form = QuestionForm()
    quiz.modified_at = datetime.utcnow()
    # Handle POST request
    if request.method == 'POST':
        # Update question text and question type
        question.text = request.form['question']
        question.question_type = request.form['question_type']
    # Check the question type and update the choices accordingly
        if question.question_type == 'true_false':
        # For yes/no questions, only two choices are needed
                correct_answer_truefalse = request.form['question_truefalse']
                for i in range(2):
                    question.choices[i].text = 'True' if i == 0 else 'False'
                    question.choices[i].is_correct = (correct_answer_truefalse == question.choices[i].text)
        if question.question_type == 'multiple_choice':
        # For multiple choice questions, update all four choices
            for i in range(4):
                question.choices[i].text = request.form[f'answer{i+1}']
                question.choices[i].is_correct = str(i+1) in request.form.getlist('correct_answer')
    # Check if at least one correct answer is selected
            if question.question_type != 'true_false':
                correct_answer = request.form.getlist('correct_answer')
                if not correct_answer:
                    flash("Please select a correct answer", 'error')
                    return redirect(url_for("crud.edit_question", quiz_id=quiz_id, question_id=question_id))

# Update correct answer choice(s)
            if question.question_type == 'true_false':
    # For yes/no questions, only two choices are needed
                correct_answer_truefalse = request.form['question_truefalse']
                for i in range(2):
                    question.choices[i].is_correct = (correct_answer_truefalse == question.choices[i].text)
            else:
    # For multiple choice questions, update all four choices
                correct_answer_list = [int(answer) for answer in request.form.getlist('correct_answer')]
                for i in range(4):
                    question.choices[i].is_correct = i+1 in correct_answer_list


        image_url = None

        if 'image' in request.files:
            print('image in request file')
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                print(filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_url = filename

            if not file and allowed_file(file.filename):
                # If image file is not allowed, show error message
                flash("Image file type not allowed. Allowed file types are png, jpg, jpeg, gif", "error")
                return render_template('quiz_details.html', quiz=quiz, form=form)

        
        else:
            print('image not in request file')

        question.image_url = image_url

        # Commit changes to database
        db.session.commit()

        # Show success message and redirect to quiz details page
        flash('Question updated successfully!', 'success')
        return redirect(url_for('crud.quiz_details', quiz_id=quiz_id))

    # Handle GET request
    return render_template('edit_question.html', question=question, form=form)

@crud.route('/delete_question/<int:quiz_id>/<int:question_id>')
@login_required
def delete_question(quiz_id, question_id):
    try:
        quiz = Quiz.query.filter_by(id=quiz_id).first()
        quiz.modified_at = datetime.utcnow()
        # Get the question and delete it from the database
        question = Question.query.get_or_404(question_id)
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted successfully!', 'success')
    except:
        # If there's an error, rollback the session and show an error message
        db.session.rollback()
        flash('Sorry, something went wrong while deleting the question', 'error')
    
    return redirect(url_for('crud.quiz_details', quiz_id=quiz_id))


@crud.route('/delete_quiz/<int:quiz_id>')
@login_required
def delete_quiz(quiz_id):
    try:
        # Get the quiz and delete it from the database
        quiz = Quiz.query.get_or_404(quiz_id)
        db.session.delete(quiz)
        db.session.commit()
        flash('Quiz deleted successfully!', 'success')
    except:
        # If there's an error, rollback the session and show an error message
        db.session.rollback()
        flash('Sorry, something went wrong while deleting the quiz', 'error')
    
    return redirect(url_for('crud.quizzes'))


@crud.route('/editQuiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def editQuiz(quiz_id):
    form = QuizForm()
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    # setting the value of current duration as a placeholder
    form.quizDuration.default = quiz.duration
    # setting the value of current description as a placeholder
    form.quizDescription.default = quiz.description
    # setting the value of current title as a placeholder
    form.quizTitle.default = quiz.title
    # setting the value of current public as a placeholder
    form.is_public.default = 'yes' if quiz.public else 'no'
    
    if form.validate_on_submit():
        try:
            quiz.title = form.quizTitle.data
            quiz.description = form.quizDescription.data
            quiz.duration = form.quizDuration.data
            quiz.public = form.is_public.data == 'yes'
            db.session.commit()
            flash('Quiz updated successfully!', 'success')
            return redirect(url_for('crud.quiz_details', quiz_id=quiz.id))
        except:
            # If there's an error, rollback the session and show an error message
            db.session.rollback()
            flash('Sorry, something went wrong while updating the quiz', 'error')
    
    # process form after validating
    form.process()
    
    return render_template('editQuiz.html', quiz=quiz, form=form)


@crud.route('/quiz/<int:quiz_id>/details')
@login_required
def quiz_details(quiz_id):
        quiz = Quiz.query.filter_by(id=quiz_id).first()
        form = QuestionForm()
                # Check if the current user is the creator of the quiz or an admin
        if current_user.admin or quiz.user_id == current_user.id:
            return render_template('quiz_details.html', quiz=quiz, form=form)
        else:
            abort(403)

@crud.route('/public_quiz/<int:quiz_id>/details')
@login_required
def public_details(quiz_id):
    try:
        quiz = Quiz.query.filter_by(id=quiz_id).first()
        form = QuestionForm()
        return render_template('public_details.html', quiz=quiz, form=form)
    except Exception as e:
        # If there's an error, print the exception message
        print(str(e))
        # Return a response to avoid the TypeError
        return "An error occurred: " + str(e), 500

