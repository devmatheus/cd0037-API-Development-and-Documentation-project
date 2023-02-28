import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404
    
    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "success": False,
            "error": 403,
            "message": "forbidden"
        }), 403
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "internal server error"
        }), 500
    
    with app.app_context():
        from models import setup_db, Question, Category

        setup_db(app)

        @app.route('/categories')
        def get_categories():
            categories = Category.query.all()
            formatted_categories = {category.id: category.format() for category in categories}
            return jsonify({
                'success': True,
                'categories': formatted_categories
            })

        @app.route('/questions')
        def get_questions():
            page = request.args.get('page', 1, type=int)
            start = (page - 1) * QUESTIONS_PER_PAGE
            end = start + QUESTIONS_PER_PAGE
            questions = Question.query.all()
            formatted_questions = [question.format() for question in questions][start:end]

            if len(formatted_questions) == 0:
                abort(404)

            categories = Category.query.all()
            formatted_categories = {category.id: category.format() for category in categories}

            return jsonify({
                'success': True,
                'questions': formatted_questions,
                'totalQuestions': len(questions),
                'categories': formatted_categories,
                'currentCategory': None
            })

        @app.route('/questions/<int:question_id>', methods=['DELETE'])
        def delete_question(question_id):
            question = Question.query.get(question_id)
            if question is None:
                abort(404)
            question.delete()
            return jsonify({
                'success': True,
                'deleted': question_id
            })

        @app.route('/questions', methods=['POST'])
        def create_question():
            body = request.get_json()
            if not ('question' in body and 'answer' in body and 'difficulty' in body and 'category' in body):
                abort(400)
            question = body.get('question')
            answer = body.get('answer')
            difficulty = body.get('difficulty')
            category = body.get('category')
            try:
                new_question = Question(question=question, answer=answer, difficulty=difficulty, category=category)
                new_question.insert()
                return jsonify({
                    'success': True,
                    'created': new_question.id
                })
            except:
                abort(422)

        @app.route('/questions/search', methods=['POST'])
        def search_questions():
            body = request.get_json()
            if not 'searchTerm' in body:
                abort(400)
            search_term = body.get('searchTerm')
            questions = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
            formatted_questions = [question.format() for question in questions]
            return jsonify({
                'success': True,
                'questions': formatted_questions,
                'totalQuestions': len(questions),
                'currentCategory': None
            })

        @app.route('/categories/<int:category_id>/questions')
        def get_questions_by_category(category_id):
            page = request.args.get('page', 1, type=int)
            start = (page - 1) * QUESTIONS_PER_PAGE
            end = start + QUESTIONS_PER_PAGE
            category = Category.query.get(category_id)
            if category is None:
                abort(404)
            questions = Question.query.filter(Question.category == str(category_id)).all()
            formatted_questions = [question.format() for question in questions][start:end]
            return jsonify({
                'success': True,
                'questions': formatted_questions,
                'totalQuestions': len(questions),
                'currentCategory': category_id
            })

        @app.route('/quizzes', methods=['POST'])
        def play_quiz():
            body = request.get_json()
            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(400)
            quiz_category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')
            if quiz_category['id'] == 0:
                questions = Question.query.all()
            else:
                questions = Question.query.filter(Question.category == str(quiz_category['id'])).all()
            formatted_questions = [question.format() for question in questions]
            random_question = random.choice(formatted_questions)
            while random_question['id'] in previous_questions:
                random_question = random.choice(formatted_questions)
            return jsonify({
                'success': True,
                'question': random_question
            })

    return app

