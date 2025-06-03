pipeline {
    agent any

    stages {
        stage('Prepare Environment') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'SECRET_KEY', variable: 'SECRET_KEY'),
                        string(credentialsId: 'DEFAULT_ADMIN_PASSWORD', variable: 'DEFAULT_ADMIN_PASSWORD'),
                        string(credentialsId: 'DEFAULT_ADMIN_LOGIN', variable: 'DEFAULT_ADMIN_LOGIN'),
                        string(credentialsId: 'POSTGRES_USERNAME', variable: 'POSTGRES_USERNAME'),
                        string(credentialsId: 'POSTGRES_PASSWORD', variable: 'POSTGRES_PASSWORD'),
                        string(credentialsId: 'POSTGRES_HOST', variable: 'POSTGRES_HOST'),
                        string(credentialsId: 'POSTGRES_DATABASE_NAME', variable: 'POSTGRES_DATABASE_NAME'),
                    ]) {
                        sh """
                        rm .env || true
                        echo "SECRET_KEY=${SECRET_KEY}" >> .env
                        echo "DEFAULT_ADMIN_LOGIN=${DEFAULT_ADMIN_LOGIN}" >> .env
                        echo "DEFAULT_ADMIN_PASSWORD=${DEFAULT_ADMIN_PASSWORD}" >> .env
                        echo "POSTGRES_USERNAME=${POSTGRES_USERNAME}" >> .env
                        echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> .env
                        echo "POSTGRES_HOST=${POSTGRES_HOST}" >> .env
                        echo "POSTGRES_DATABASE_NAME=${POSTGRES_DATABASE_NAME}" >> .env
                        """
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t \\"calorie-tracker-backend\\" .'
            }
        }

        stage('Stop and Remove Existing Container') {
            steps {
                sh 'docker stop calorie-tracker-backend || true'
                sh 'docker rm calorie-tracker-backend || true'
            }
        }

        stage('Run New Container') {
            steps {
                sh 'docker run -d --name \\"calorie-tracker-backend\\" -p 8001:8001 \\"calorie-tracker-backend\\" --root-path \\"/api\\"'
            }
        }
    }
}