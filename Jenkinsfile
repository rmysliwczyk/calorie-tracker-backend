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
                        string(credentialsId: 'DATABASE_URL', variable: 'DATABASE_URL')
                    ]) {
                        sh """
                        rm .env || true
                        echo "SECRET_KEY=${SECRET_KEY}" >> .env
                        echo "DEFAULT_ADMIN_LOGIN=${DEFAULT_ADMIN_LOGIN}" >> .env
                        echo "DEFAULT_ADMIN_PASSWORD=${DEFAULT_ADMIN_PASSWORD}" >> .env
                        echo "DATABASE_URL=${DATABASE_URL}" >> .env
                        """
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t \"calorie-tracker-backend\" .'
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
                sh 'docker run -d --name \"calorie-tracker-backend\" -p 8001:8001 \"calorie-tracker-backend\" --root-path \"/api\" --restart always'
            }
        }
    }
}