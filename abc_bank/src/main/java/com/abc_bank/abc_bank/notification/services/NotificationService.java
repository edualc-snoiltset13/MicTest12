package com.abc_bank.abc_bank.notification.services;

import com.abc_bank.abc_bank.auth_users.entity.User;
import com.abc_bank.abc_bank.notification.dtos.NotificationDTO;

public interface NotificationService {
    void sendEmail(NotificationDTO notificationDTO, User user);
}
